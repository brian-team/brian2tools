import re
from os import getcwd
from copy import deepcopy
from os.path import abspath, dirname, join, exists
import itertools

import neuroml.loaders as loaders
from neuroml.utils import validate_neuroml2
from brian2 import Morphology, SpatialNeuron
from brian2.utils.logger import get_logger
from brian2.spatialneuron.morphology import Section
from brian2.units import *
from brian2.equations.equations import Equations
from brian2tools.nmlutils.utils import string_to_quantity

from .helper import *

logger = get_logger(__name__)


class ValidationException(Exception):
    pass


def validate_morphology(segments):
    """
    Validates if the segments are connected to each other or not.

    Parameters
    ----------
    segments : list
        list of segments present in a morphology

    Returns
    -------
    """

    try:
        start_segment = None
        for segment in segments:

            if segment.parent is not None:
                if segment.parent.fraction_along not in [0, 1]:
                    raise NotImplementedError(
                        "{0} has fraction along value {1} which is not "
                        "supported!!".
                            format(segment, segment.parent.fraction_along))
            elif start_segment is not None:
                raise ValidationException(
                    "Two segments with parent id as -1 (i.e no parent): "
                    "{0} and {1}".
                        format(formatter(start_segment), formatter(segment)))
            else:
                start_segment = segment
                logger.info(
                    "starting segment is {0}".format(formatter(segment)))

    except ValidationException as v:
        logger.error("Validation error: {0}".format(v))
        raise

    except Exception as e:
        logger.error("Exception occured: {0}".format(e))
        raise


class NMLMorphology(object):
    """
        A class that extracts and store all morphology related information
        from a .nml file.
    """

    class SectionObject(object):
        def __init__(self):
            """
            Initializes a sectionObject which is used internally to group
            related segments.
            """
            self.sectionList = []
            self.segmentList = []
            self.name = 'soma'

    def __init__(self, file_obj, name_heuristic=True):
        """
        Initializes NMLMorphology Class
        Parameters
        ----------
        file_obj: str
            nml file path or a file object
        name_heuristic: bool
            When this parameter is set to True morphology sections
            will be determined based on the segment names. In this case
            Section name will be created by combining names of the inner
            segments of the section. When set to False, all linearly
            connected segments combines to form a section and naming
            convention sec{unique_integer} is followed.
        """
        self.file_obj = file_obj
        self.name_heuristic = name_heuristic
        self.incremental_id = 0
        self.doc = self._get_nml_doc(self.file_obj)
        cell = self.doc.cells[0]
        self.morph = cell.morphology
        self.segments = self._adjust_morph_object(self.morph.segments)

        section = self.SectionObject()
        self.seg_dict = self._get_segment_dict(self.segments)
        self.children = get_child_segments(self.segments)
        self.root = self._get_root_segment(self.segments)
        self.section = self._create_tree(section, self.root)
        self.morphology = self.build_morphology(self.section)
        self.segment_groups = self.get_resolved_group_ids(self.morph)

        # biophysical Properties
        self.properties = self._get_properties(cell.biophysical_properties)
        self.channel_properties = self._get_channel_props(
            cell.biophysical_properties.membrane_properties.channel_densities)

    def _get_nml_doc(self, file_obj):
        """
        Helper function to read .nml file and return document object.

        Parameters
        ----------
        file_obj: str
            File path or file object.

        Returns
        -------
        dict
            A dictionary containing all the information extracted from the
            given .nml file.

        """

        def merge_dicts(parent, child):
            z = child.copy()
            z.update(parent)
            return z

        def append_doc(doc, included_doc):
            doc_vars = vars(doc)
            for key, value in vars(included_doc).items():
                if value:  # checks for empty list/dict
                    if key not in doc_vars:
                        updated_val = value
                    else:
                        if not doc_vars[key]:  # if list/dict in doc is empty
                            updated_val = value
                        elif isinstance(doc_vars[key], list):
                            doc_vars[key] += value
                            updated_val = doc_vars[key]
                        elif isinstance(doc_vars[key], dict):
                            doc_vars[key] = merge_dicts(doc_vars[key], value)
                            updated_val = doc_vars[key]
                        else:
                            updated_val = doc_vars[key]
                    setattr(doc, key, updated_val)

        file_dir = getcwd()
        if isinstance(file_obj, str):
            file_dir = dirname(abspath(file_obj))

        if isinstance(file_obj, str):
            # Generate absolute path if not provided already
            file_obj = abspath(file_obj)

        # Validating NeuroML file
        validate_neuroml2(deepcopy(file_obj))
        logger.info("Validated provided .nml file")

        # Load nml file
        doc = loaders.NeuroMLLoader.load(file_obj)
        logger.info("Loaded morphology")

        if not doc.includes:
            return doc
        else:
            for f in doc.includes:
                file_path = join(file_dir, f.href)
                if exists(file_path):
                    included_doc = self._get_nml_doc(file_path)
                    append_doc(doc, included_doc)
                else:
                    logger.warn(
                        "Included file `{}` does not exist at path `{"
                        "}`".format(f.href, file_path))

        return doc

    def build_morphology(self, section, parent_section=None):
        """
        A recursive function that converts Section tree to a Brian Morphology
        object.

        Parameters
        ----------
        section: SectionObject
            An object of class SectionObject containing segment member
            information.

        parent_section: SectionObject
            Parent of the section object passed.

        Returns
        -------
        Morphology
            Generated Brian morphology object.
        """

        sec = self._build_section(section, parent_section)
        for s in section.sectionList:
            sec[s.name] = self.build_morphology(s, section)
        return sec

    def get_segment_group_ids(self, group_id, morph):
        """
        Returns segment ids of all segments of a SegmentGroup with id
        `group_id` present in .nml file.

        Parameters
        ----------
        group_id: str
            SegmentGroup's id/name whose information is required.
        morph: Morphology
            Brian's morphology object created from .nml file.
        Returns
        -------
        list
            List of segment ids
        """

        # Appends member segment ids to list.
        def resolve_member(mem_list, members):
            if members is not None:
                for m in members:
                    mem_list.append(m.segments)

        # Resolves SegmentGroup's included inside parent SegmentGroup.
        def resolve_includes(l, grp, m):
            if grp.includes is not None:
                for g in grp.includes:
                    resolve_includes(l, self._get_segment_group(m,
                                                                g.segment_groups),
                                     m)
            resolve_member(l, grp.members)

        id_list = []
        for g in morph.segment_groups:
            if g.id == group_id:
                resolve_includes(id_list, g, morph)
                resolve_member(id_list, g.members)
        return id_list

    def get_resolved_group_ids(self, m):
        """
        Returns dictionary of relative ids(i.e ids used inside Brian's
        morphology) of all segments in each SegmentGroup present in given
        morphology object.

        Returns
        -------
        dict
            A dictionary of resolved segment ids of each SegmentGroup,
            here each SegmentGroup's id is a key of this dictionary.
        """

        # Returns id mappings of segments present in .nml file
        def get_id_mappings(segments, parent_node=None, counter=0):
            if parent_node is None:
                parent_node = self._get_root_segment(segments).id

            mapping = {}
            children = get_child_segments(segments)
            self._perform_dfs(mapping, parent_node, counter, children)
            return mapping

        resolved_ids = {}
        for group in m.segment_groups:
            grp_ids = self.get_segment_group_ids(group.id, m)
            id_map = get_id_mappings(m.segments)
            resolved_ids[group.id] = list(set([id_map[grp_id] for grp_id in
                                               grp_ids]))
        return resolved_ids

    def _is_heuristically_sep(self, section, seg_id):
        """
        Helper function that determines if the given segment belongs to the
        passed section or not as per our heuristic.

        Parameters
        ----------
        section: SectionObject
            Object of class SectionObject that contains information about
            segments belonging to same section.
        seg_id: int
            segment id of given segment

        Returns
        -------
        bool
            Returns true if the given segment is not heuristically connected
            to the provided section.
        """
        root_name = section.name.rstrip('0123456789_')
        seg = self.seg_dict[self.children[seg_id][0]]
        return not seg.name.startswith(root_name)

    def _get_section_name(self, seg_id):
        """
        Helper function that generate the new section name based on whether
        name_heuristic is set to True or not.

        Parameters
        ----------
        seg_id: int
            segment id of concerned segment.

        Returns
        -------
        str
            generated section name.
        """
        if not self.name_heuristic:
            self.incremental_id = self.incremental_id + 1
            return "sec" + str(self.incremental_id)
        return self.seg_dict[seg_id].name

    def _create_tree(self, section, seg):
        """
        Helper function that creates a section tree where each section node can
        have multiple child segments and each section may be connected to
        multiple other sections

        Parameters
        ----------
        section: SectionObject
            Object of class SectionObject that contains information about
            segments belonging to same section.
        seg: Segment
            Segment object belongs to the given section and its
        children's are resolved to create further tree nodes.

        Returns
        -------
        SectionObject
            created section tree.
        """

        # abstracts the initialization step of a section
        def intialize_section(section, seg_id):
            sec = self.SectionObject()
            sec.name = self._get_section_name(seg_id)
            section.sectionList.append(sec)
            return sec

        section.segmentList.append(seg)
        if len(self.children[seg.id]) > 1 or seg.name == "soma":
            for seg_id in self.children[seg.id]:
                self._create_tree(intialize_section(section, seg_id),
                                  self.seg_dict[seg_id])
        elif len(self.children[seg.id]) == 1:
            if self.name_heuristic:
                if self._is_heuristically_sep(section, seg.id):
                    self._create_tree(intialize_section(section, seg.id),
                                      self.seg_dict[self.children[seg.id][0]])
                else:
                    seg_name = self.seg_dict[self.children[seg.id][0]].name
                    # separate integer from the end of segment name
                    m = re.search(r'\d+$', seg_name)
                    section.name = '{}_{}'.format(section.name, m.group())
                    self._create_tree(section,
                                      self.seg_dict[self.children[seg.id][0]])
            else:
                self._create_tree(section,
                                  self.seg_dict[self.children[seg.id][0]])
        return section

    def _build_section(self, section, section_parent):
        """
        This function generates Brian's morphology section from given section
        object of class SectionObject.

        Parameters
        ----------
        section: SectionObject
            given sectionObject that needs to be converted to Brian's section object.
        section_parent: SectionObject
            parent of the given sectionObject.

        Returns
        -------
        Section
            Brian's section object.
        """
        shift = section.segmentList[0].proximal
        x, y, z = [0], [0], [0]
        diameter = [section_parent.segmentList[-1].distal.diameter if
                    section_parent is not None else section.segmentList[
            0].proximal.diameter]

        for s in section.segmentList:
            x.append(s.distal.x - shift.x)
            y.append(s.distal.y - shift.y)
            z.append(s.distal.z - shift.z)
            diameter.append(s.distal.diameter)
        return Section(n=len(section.segmentList), x=x * um, y=y * um, z=z * um,
                       diameter=diameter * um)

    # Generate proximal points for a segment if not present already
    def _adjust_morph_object(self, segments):
        for segment in segments:
            if segment.proximal is None:
                if segment.parent is not None:
                    parent_seg = get_parent_segment(segment, segments)
                    segment.proximal = parent_seg.distal
                else:
                    raise ValueError(
                        "Segment {0} has no parent and no proximal "
                        "point".format(segment))
        return segments

    # Performs Depth-first traversal on segment node and its child segments
    def _perform_dfs(self, mapping, node, counter, children):
        mapping[node] = counter
        new_counter = counter + 1
        for child in children[node]:
            new_counter = self._perform_dfs(mapping, child, new_counter,
                                            children)
        return new_counter

    # Returns segment dictionary with each segment's id as key
    def _get_segment_dict(self, segments):
        segdict = {}
        for s in segments:
            segdict[s.id] = s
        return segdict

    # Returns SegmentGroup object corresponding to given group id.
    def _get_segment_group(self, m, grp_id):
        for g in m.segment_groups:
            if g.id == grp_id:
                return g

    # Returns parent/root segment object.
    def _get_root_segment(self, segments):
        for x in segments:
            if x.parent is None:
                return x

    # Prints Section Tree information, for visualization.
    def printtree(self, section):
        for s in section.segmentList:
            print(s.id)
        print("end section")
        print("section list: {}".format(section.sectionList))
        for sec in section.sectionList:
            self.printtree(sec)

    def _get_properties(self, bio_prop):
        """
        Extract properties like threshold, refractory, Ri and Cm and returns
        a dictionary of these properties.

        Parameters
        ----------
        bio_prop: Biophysical_properties
            Properties object obtained from given .nml file

        Returns
        -------
        dict
            Biophysical properties dictionary
        """
        prop = {}

        def get_dict(obj_list):
            d = {}
            for o in obj_list:
                d[o.segment_groups] = string_to_quantity(o.value)
            return d

        self.Ri = get_dict(bio_prop.intracellular_properties.resistivities)
        self.Cm = get_dict(bio_prop.membrane_properties.specific_capacitances)
        if len(bio_prop.membrane_properties.spike_threshes) == 1:
            self.threshold = string_to_quantity(
                bio_prop.membrane_properties.spike_threshes[0].value)
            self.threshold_string = 'v > {}'.format(repr(self.threshold))
            prop["threshold"] = self.threshold_string
            prop["refractory"] = self.threshold_string
        if len(self.Cm) == 1:
            prop["Cm"] = self.Cm[list(self.Cm.keys())[0]]
        if len(self.Ri) == 1:
            prop["Ri"] = self.Ri[list(self.Ri.keys())[0]]

        return prop

    def set_neuron_properties(self, neuron, name, value_dict):
        """
        Method to apply properties present in given dictionary to the
        spatialNeuron provided.

        Parameters
        ----------
        neuron_prop: SpatialNeuron
            SpatialNeuron object on which you want to apply these properties.
        name : str
            Name of the property that should be set.
        value_dict: dict
            Dictionary of properties to be applied.
        """
        for segment_group, value in value_dict.items():
            ids = self.segment_groups[segment_group]
            if len(ids):
                getattr(neuron, name)[ids] = value

    def _get_channel_props(self, channels):
        """
        Returns dictionaries mapping segment groups to `channel density` and
        `erev` properties.

        Parameters
        ----------
        channels: list
            list of channels present in .nml file

        Returns
        -------
        dict
            Mapping from segment groups to g_... and E_... attributes of the
            various channels
        """
        properties = defaultdict(dict)
        for c in channels:
            properties[c.segment_groups]['g_' + c.ion_channel] = string_to_quantity(
                c.cond_density)
            properties[c.segment_groups]['E_' + c.ion_channel] = string_to_quantity(
                c.erev)
        return dict(properties)

    def get_channel_equations(self, ion_channel):
        """
        This method extracts information for the `ion_channel id` passed as
        argument, convert required values to `quantity` objects and substitute
        it in its corresponding template to generate ion channel equations.
        Currently this method only support ion channels of type
        `ionChannelHH` and `ionChannelPassive`.

        Parameters
        ----------
        ion_channel: str
            ion channel id.

        Returns
        -------
        Equations
            equation object for the given ion channel.
        """
        channel_obj = None
        for c in itertools.chain(self.doc.ion_channel, self.doc.ion_channel_hhs):
            if c.id == ion_channel:
                channel_obj = c
                break
        if channel_obj is None:
            err = ("ion channel `{}` not found. List of ion channel present "
                   "here:\n {}").format(ion_channel,
                                        [c.id for c in
                                         itertools.chain(getattr(self.doc, 'ion_channel', []),
                                                         getattr(self.doc, 'ion_channel_hhs', []))])
            logger.error(err)
            raise ValueError(err)

        if channel_obj in getattr(self.doc, 'ion_channel', []):
            channel_type = channel_obj.type
        else:
            if len(channel_obj.gates) == 0 and channel_obj.species is None:
                channel_type = 'ionChannelPassive'
            else:
                channel_type = 'ionChannelHH'

        if channel_type in ['ionChannelHH', 'ionChannel']:
            values = {}

            def rename_var(v):
                return '{}_{}'.format(v, ion_channel)

            def _gate_value_str(gate_list):
                str_list = []
                s = ''

                for g in gate_list:
                    renamed_gate = rename_var(g.id)
                    if g.instances == 1:
                        s += "*{}".format(renamed_gate)
                    else:
                        s += '*{}**{}'.format(renamed_gate, g.instances)

                    # gating information
                    str_list.append("d{0}/dt = alpha_{0}*(1-{0}) - beta_{0}*"
                                    "{0} : 1".format(renamed_gate))

                    for r in [g.forward_rate, g.reverse_rate]:
                        mode = 'alpha' if r is g.forward_rate else 'beta'
                        if r is None:
                            raise NotImplementedError('Only gates defined with '
                                                      'forward and reverse rates '
                                                      'are supported at the moment.')
                        if r.type == 'HHSigmoidRate':
                            str_list.append(
                                "{0}_{1} = rate_{0}_{1} / (1 + exp(0 "
                                "- ("
                                "v - midpoint_{0}_{1})/scale_{0}_{1})) : "
                                "second**-1".format(mode, renamed_gate))

                        elif r.type == 'HHExpRate':
                            str_list.append(
                                "{0}_{1} = rate_{0}_{1} * exp((v - "
                                "midpoint_{0}_{1})/scale_{0}_{1}) : "
                                "second**-1".format(mode, renamed_gate))

                        elif r.type == 'HHExpLinearRate':
                            str_list.append(
                                "{0}_{1} = rate_{0}_{1} * (v - midpoint_{0}_{1}) / "
                                "scale_{0}_{1} / (1 - exp(- (v - midpoint_{0}_{1}) / "
                                "scale_{0}_{1})) : "
                                "second**-1".format(mode, renamed_gate))
                        else:
                            raise NotImplementedError(
                                "Rate of type `{}` is currently not supported. Supported "
                                "rate types are: {}".format(r.type,
                                                            ['HHSigmoidRate',
                                                             'HHExpLinearRate',
                                                             'HHExpRate']))

                        # add values to dictionary
                        values['rate_{0}_{1}'.format(mode, renamed_gate)] = \
                            string_to_quantity(r.rate)
                        values['midpoint_{0}_{1}'.format(mode, renamed_gate)] = \
                            string_to_quantity(r.midpoint)
                        values['scale_{0}_{1}'.format(mode, renamed_gate)] = \
                            string_to_quantity(r.scale)

                s = s[1:] if s.startswith('*') else s
                return s, str_list

            gate_str, str_list = _gate_value_str(itertools.chain(channel_obj.gates,
                                                                 channel_obj.gate_hh_rates))

            I = '{} = {}*{}*({} - v): amp / meter ** 2'.format(rename_var(
                'I'), rename_var('g'), gate_str, rename_var('E'))
            str_list = [I] + str_list
            str_list.append("{} : siemens/meter**2 (constant)".format(rename_var('g')))
            str_list.append("{} : volt (constant)".format(rename_var('E')))
            eq = Equations('\n'.join(str_list), **values)

        elif channel_type == 'ionChannelPassive':
            new_I = 'I_{}'.format(ion_channel)
            conductance = string_to_quantity(channel_obj.conductance)

            erev = None
            for properties in self.channel_properties.values():
                erev_name = 'E_{}'.format(ion_channel)
                if erev_name in properties:
                    if erev is None:
                        erev = properties[erev_name]
                    elif erev != properties[erev_name]:
                        raise NotImplementedError("Only a single value "
                                                  "for reversal potential '{}' "
                                                  "is supported.".format(erev_name))
            if erev is None:
                raise ValueError("No value for reversal potential '{}' "
                                 "found.".format(erev_name))

            eq = Equations('I = g/area*(erev - v) : amp/meter**2', I=new_I,
                           g=conductance, erev=erev)

        else:
            raise NotImplementedError("Requested ion Channel is of type `{}`,"
                                      " which is currently not supported. Currently this library "
                                      "supports ion channels of type: `{}`".format(
                channel_type, ['ionChannelPassive', 'ionChannelHH']))

        return eq
