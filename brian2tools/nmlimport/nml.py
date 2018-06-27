import neuroml.loaders as loaders
from neuroml.utils import validate_neuroml2
from brian2 import Morphology
from brian2.utils.logger import get_logger
from os.path import abspath
from .helper import *
from copy import deepcopy
import re
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
                if segment.parent.fraction_along not in [0,1]:
                    raise NotImplementedError(
                        "{0} has fraction along value {1} which is not "
                        "supported!!".
                        format(segment,segment.parent.fraction_along))

                seg_parent = get_parent_segment(segment, segments)

                if not are_segments_joined(segment, seg_parent):
                    raise ValidationException(
                        "{0} and its parent segment {1} are not connected!!".
                        format(formatter(segment), formatter(seg_parent)))

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


class NmlMorphology(object):
    """
        A class that extracts and store all morphology related information
        from a .nml file.
    """



    class SectionObject(object):
        def __init__(self):
            self.sectionList = []
            self.segmentList = []
            self.name = 'soma'

    def __init__(self, file_obj, name_heuristic=True):
        """
        Initializes NmlMorphology Class
        Parameters
        ----------
        file_obj: str
            nml file path or a file object
        name_heuristic: bool
            If true morphology sections will be determined based on the
            segment names and section name will be created by combining names of
            the inner segments of the section.
        """
        self.name_heuristic = name_heuristic
        self.incremental_id = 0
        self.doc = self._get_morphology_dict(file_obj)
        self.morph = self.doc.cells[0].morphology
        self.segments = self._adjust_morph_object(self.morph.segments)

        section = self.SectionObject()
        self.seg_dict = self._get_segment_dict(self.segments)
        self.children = get_child_segments(self.segments)
        self.root = self._get_root_segment(self.segments)
        self.section = self._create_tree(section, self.root)
        # self.printtree(self.section)
        self.morphology_obj = self.build_morphology(self.section)
        self.resolved_grp_ids=self.get_resolved_group_ids(self.morph)

    # Helper function to read .nml file and return document object
    def _get_morphology_dict(self, file_obj):
        if isinstance(file_obj, str):
            # Generate absolute path if not provided already
            file_obj = abspath(file_obj)

            # Validating NeuroML file
        validate_neuroml2(deepcopy(file_obj))
        logger.info("Validated provided .nml file")

        # Load nml file
        doc = loaders.NeuroMLLoader.load(file_obj)
        logger.info("Loaded morphology")
        return doc

    def _is_heurestically_sep(self, section, seg_id):
        root_name = section.name.rstrip('0123456789_')
        seg = self.seg_dict[self.children[seg_id][0]]
        return not seg.name.startswith(root_name)

    def _get_section_name(self, seg_id):
        if not self.name_heuristic:
            self.incremental_id = self.incremental_id + 1
            return "sec" + str(self.incremental_id)
        return self.seg_dict[seg_id].name

    def _create_tree(self, section, seg):

        def intialize_section(section, seg_id):
            sec = self.SectionObject()
            sec.name = self._get_section_name(seg_id)
            section.sectionList.append(sec)
            return sec

        section.segmentList.append(seg)
        # print(section.name)
        if len(self.children[seg.id]) > 1 or seg.name == "soma":
            for seg_id in self.children[seg.id]:
                self._create_tree(intialize_section(section, seg_id),
                                  self.seg_dict[seg_id])
        elif len(self.children[seg.id]) == 1:
            if self.name_heuristic:
                if self._is_heurestically_sep(section, seg.id):
                    self._create_tree(intialize_section(section, seg.id),
                                      self.seg_dict[self.children[seg.id][0]])
                else:
                    seg_name = self.seg_dict[self.children[seg.id][0]].name
                    m = re.search(r'\d+$', seg_name)
                    section.name = '{}_{}'.format(section.name, m.group())
                    self._create_tree(section,
                                      self.seg_dict[self.children[seg.id][0]])
            else:
                self._create_tree(section,
                                  self.seg_dict[self.children[seg.id][0]])
        return section

    def _build_section(self, section, section_parent):
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

    def build_morphology(self, section, parent_section=None):

        sec = self._build_section(section, parent_section)
        for s in section.sectionList:
            sec[s.name] = self.build_morphology(s, section)
        return sec

    def printtree(self, section):
        for s in section.segmentList:
            print(s.id)
        print("end section")
        print("section list: {}".format(section.sectionList))
        for sec in section.sectionList:
            self.printtree(sec)

    # Returns segment ids of a segment group present in .nml file
    def get_segment_group_ids(self,group_id, morph):

        def resolve_member(mem_list, members):
            if members is not None:
                for m in members:
                    mem_list.append(m.segments)

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

    # Get resolved ids for a group in a file, ex. pass `apical_dends`,`pyr_4_sym.cell.nml`
    def get_resolved_group_ids(self, m):

        # Return id mappings of segments present in .nml file
        def get_id_mappings(segments, parent_node=None, counter=0):
            if parent_node is None:
                parent_node = self._get_root_segment(segments).id

            mapping = {}
            children = get_child_segments(segments)
            self._perform_dfs(mapping, parent_node, counter, children)
            return mapping

        resolved_ids={}
        for group in m.segment_groups:
            grp_ids = self.get_segment_group_ids(group.id, m)
            id_map = get_id_mappings(m.segments)
            resolved_ids[group.id]= list(set([id_map[grp_id] for grp_id in
                                         grp_ids]))
        return resolved_ids


    # Generate proximal points for a segment if not present already
    def _adjust_morph_object(self,segments):
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

    def _perform_dfs(self,mapping, node, counter, children):
        mapping[node] = counter
        new_counter = counter + 1
        for child in children[node]:
            new_counter = self._perform_dfs(mapping, child, new_counter,
                                           children)
        return new_counter

    def _get_segment_dict(self,segments):
        segdict = {}
        for s in segments:
            segdict[s.id] = s
        return segdict

    def _get_segment_group(self,m, grp):
        for g in m.segment_groups:
            if g.id == grp:
                return g

    def _get_root_segment(self,segments):
        for x in segments:
            if x.parent is None:
                return x

