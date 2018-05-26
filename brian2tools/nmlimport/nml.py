import neuroml.loaders as loaders
from neuroml.utils import validate_neuroml2
from brian2 import *
from brian2.utils.logger import get_logger
from os.path import abspath
from .helper import *

logger = get_logger(__name__)


class ValidationException(Exception):
    pass


# Validating morphology segments positioning
def validate_morphology(segments):
    try:
        start_segment = None
        for segment in segments:
            if segment.parent != None:
                seg_parent = get_parent_segment(segment, segments)

                if not are_segments_joined(segment, seg_parent):
                    raise ValidationException("{0} and its parent "
                                              "segment {1} are not connected!!".
                                              format(formatter(segment),
                                                     formatter(seg_parent)))

            elif start_segment != None:
                raise ValidationException("Two segments with parent id "
                                          "as -1 (i.e no parent): {0} and {1}".
                                          format(formatter(start_segment)
                                                 , formatter(segment)))
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


# Generate morphology object from given cell
def generate_morph_object(cell):
    # sort segment list in ascending order of id
    sorted_segments = sorted(cell.morphology.segments, key=lambda x: x.id)
    logger.info("Sorted segments are: {0}".format(formatter(sorted_segments)))
    points = get_tuple_points(sorted_segments)

    return Morphology.from_points(points, spherical_soma=False)


# Generate tuple of points from segments
def get_tuple_points(segments):
    # tuple generation
    points = ()

    # validate morphology
    validate_morphology(segments)

    # generate initial tuple
    seg = segments[0]
    point = (seg.id, seg.name, seg.proximal.x , seg.proximal.y, seg.proximal.z, seg.proximal.diameter, -1 if seg.parent == None else seg.parent.segments)
    points = points + (point,)

    # iterate over morphology segments
    for segment in segments:
        point = (segment.id + 1, segment.name, segment.distal.x , segment.distal.y, segment.distal.z, segment.distal.diameter, 0 if segment.parent == None else segment.parent.segments + 1)
        points = points + (point,)

    logger.info("Sequence of points sent to `from_points` function: \n{0}"
                .format(formatter(points)))

    return points


# Return morphology object present in cell specified by cell_id
def load_morph_from_cells(cells, cell_id=None):
    if cell_id == None:
        return generate_morph_object(cells[0])
    for cell in cells:
        if (cell_id == cell.id):
            return generate_morph_object(cell)

    err = ("The cell id you specified {0} doesn't exist."
           " Present cell id's are:\n {1}".format(formatter(cell_id),
                                                  formatter([cell.id for cell in
                                                             cells])))
    logger.error('Value error: %s' % err)

    raise ValueError(err)


# Returns final morphology object
def load_morphology(nml_file, cell_id=None):
    # Generate absolute path if not provided already
    nml_file = abspath(nml_file)

    # Validating NeuroML file
    validate_neuroml2(nml_file)
    logger.info("Validated provided .nml file")

    # Load nml file
    doc = loaders.NeuroMLLoader.load(nml_file)
    logger.info("Loaded morphology file from: {0}".format(nml_file))

    if size(doc.cells) > 1:
        if cell_id != None:
            return load_morph_from_cells(doc.cells, cell_id=cell_id)
        morphologies = {}
        for cell in doc.cells:
            morphologies[cell.id] = load_morph_from_cells(doc.cells,
                                                          cell_id=cell.id)
        return morphologies

    elif size(doc.cells) == 1:
        return load_morph_from_cells(doc.cells, cell_id=cell_id)
