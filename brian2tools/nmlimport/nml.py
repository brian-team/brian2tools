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
                if segment.parent.fraction_along != 1:
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


def get_tuple_points(segments):
    """
     Generates a tuple of points corresponding to each segment.

    Parameters
    ----------
    segments : list
        list of segments present in a morphology

    Returns
    -------
    tuple
        a tuple of points
    """

    points = ()

    # adjust morphology
    segments = adjust_morph_object(segments)

    # validate morphology
    validate_morphology(segments)

    # generate initial tuple
    seg = segments[0]
    point = (seg.id,
             seg.name,
             seg.proximal.x, seg.proximal.y, seg.proximal.z,
             seg.proximal.diameter,
             -1 if seg.parent is None else seg.parent.segments)

    points = points + (point,)

    # iterate over morphology segments
    for segment in segments:
        point = (
            segment.id + 1,
            segment.name if segment.name == 'soma' else 'unknown',
            segment.distal.x, segment.distal.y,segment.distal.z,
            segment.distal.diameter,
            seg.id if segment.parent is None else segment.parent.segments + 1)

        points = points + (point,)
    logger.info("Sequence of points sent to `from_points` function: \n{0}"
                .format(formatter(points)))

    return points


def generate_morph_object(cell):
    """
    Generate morphology object from a given cell.

    Parameters
    ----------
    cell : dict
        a python cell object.

    Returns
    -------
    Morphology
        morphology obtained from the cell.
    """

    # sort segment list in ascending order of id
    sorted_segments = sorted(cell.morphology.segments, key=lambda x: x.id)
    logger.info("Sorted segments are: {0}".format(formatter(sorted_segments)))
    points = get_tuple_points(sorted_segments)

    return Morphology.from_points(points, spherical_soma=False)


def load_morph_from_cells(cells, cell_id=None):
    """
    Returns morphology object present in cell specified by cell_id.

    Parameters
    ----------
    cells : list
        a list of cell objects.
    cell_id : str
        id of a cell whose morphology is required.

    Returns
    -------
    Morphology
        morphology object obtained from the cell.
    """

    if cell_id is None:
        return generate_morph_object(cells[0])
    for cell in cells:
        if cell_id == cell.id:
            return generate_morph_object(cell)

    err = (
        "The cell id you specified {0} doesn't exist. Present cell id's "
        "are:\n {1}"
        .format(formatter(cell_id), formatter([cell.id for cell in cells])))

    logger.error('Value error: %s' % err)
    raise ValueError(err)


def load_morphology(file_obj, cell_id=None):
    """
    Generates morphology object from a file or a file object.

    When passing a file object to load morphology, make sure *is_obj* param
    is set to True.

    Parameters
    ----------
    file_obj : str
        .nml file location or file object containing morphology information.
    cell_id : str
        id of a cell whose morphology we need.

    Returns
    -------
    Morphology
        a morphology object obtained from the cell.
    """

    if isinstance(file_obj,str):
        # Generate absolute path if not provided already
        file_obj = abspath(file_obj)

    # Validating NeuroML file
    validate_neuroml2(deepcopy(file_obj))
    logger.info("Validated provided .nml file")

    # Load nml file
    doc = loaders.NeuroMLLoader.load(file_obj)
    logger.info("Loaded morphology")

    if len(doc.cells) > 1:
        if cell_id is not None:
            return load_morph_from_cells(doc.cells, cell_id=cell_id)
        morphologies = {}
        for cell in doc.cells:
            morphologies[cell.id] = load_morph_from_cells(doc.cells,
                                                          cell_id=cell.id)
        return morphologies

    elif len(doc.cells) == 1:
        return load_morph_from_cells(doc.cells, cell_id=cell_id)


# Returns segment ids of a segment group present in .nml file
def get_segment_group_ids(group_id, morph):
    id_list = []
    for g in morph.segment_groups:
        if g.id == group_id:
            resolve_includes(id_list, g, morph)
            resolve_member(id_list, g.members)
    return id_list


# Get resolved ids for a group in a file, ex. pass `apical_dends`,`pyr_4_sym.cell.nml`
def get_resolved_group_ids(group, file_obj):
    doc = loaders.NeuroMLLoader.load(file_obj)
    m = doc.cells[0].morphology
    grp_ids = get_segment_group_ids(group,m)
    id_map = get_id_mappings(m.segments)
    return [id_map[grp_id] for grp_id in grp_ids]


class SectionObject(object):
    def __init__(self):
        self.sectionList=[]
        self.segmentList=[]
        self.name='soma'


class MorphologyTree(object):

    def __init__(self, file_obj, name_heuristic=True):
        self.name_heuristic = name_heuristic
        self.incremental_id = 0
        self.doc = self._get_morphology_dict(file_obj)
        self.morph = self.doc.cells[0].morphology
        self.segments = adjust_morph_object(self.morph.segments)

        section = SectionObject()
        self.seg_dict = get_segment_dict(self.segments)
        self.children = get_child_segments(self.segments)
        self.root = get_root_segment(self.segments)
        self.section = self._create_tree(section, self.root)
        # self.printtree(self.section)
        self.morphology_obj = self.build_morphology(self.section)
        self.resolved_grp_ids=self.get_resolved_group_ids(self.morph)

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
            sec = SectionObject()
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
        id_list = []
        for g in morph.segment_groups:
            if g.id == group_id:
                resolve_includes(id_list, g, morph)
                resolve_member(id_list, g.members)
        return id_list

    # Get resolved ids for a group in a file, ex. pass `apical_dends`,`pyr_4_sym.cell.nml`
    def get_resolved_group_ids(self, m):
        resolved_ids={}
        for group in m.segment_groups:
            grp_ids = get_segment_group_ids(group.id, m)
            id_map = get_id_mappings(m.segments)
            resolved_ids[group.id]= list(set([id_map[grp_id] for grp_id in
                                         grp_ids]))
        return resolved_ids
