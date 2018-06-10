import neuroml.loaders as loaders
from neuroml.utils import validate_neuroml2
from brian2 import Morphology
from brian2.utils.logger import get_logger
from os.path import abspath
from .helper import *
from copy import deepcopy

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
    point = (seg.id, seg.name, seg.proximal.x, seg.proximal.y, seg.proximal.z,
             seg.proximal.diameter,
             -1 if seg.parent is None else seg.parent.segments)

    points = points + (point,)

    # iterate over morphology segments
    for segment in segments:
        point = (
            segment.id + 1, segment.name, segment.distal.x, segment.distal.y,
            segment.distal.z, segment.distal.diameter,
            0 if segment.parent is None else segment.parent.segments + 1)

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
