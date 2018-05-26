from copy import deepcopy
import neuroml.loaders as loaders
from brian2tools.nmlimport.nml import *
from pytest import mark, raises

POINTS=((0, 'soma', 0.0, 0.0, 0.0, 23.0, -1),
        (1, 'soma', 0.0, 17.0, 0.0, 23.0, 0),
        (2, 'apical0', 0.0, 77.0, 0.0, 6.0, 1),
        (3, 'apical2', 0.0, 477.0, 0.0, 4.4, 2),
        (4, 'apical3', 0.0, 877.0, 0.0, 2.9, 3),
        (5, 'apical4', 0.0, 1127.0, 0.0, 2.0, 4),
        (6, 'apical1', -150.0, 77.0, 0.0, 3.0, 2),
        (7, 'basal0', 0.0, -50.0, 0.0, 4.0, 1),
        (8, 'basal1', 106.07, -156.07, 0.0, 5.0, 7),
        (9, 'basal2', -106.07, -156.07, 0.0, 5.0, 7))


nml_obj= loaders.NeuroMLLoader.load(abspath(("sample1.cell.nml")))
morph_obj= nml_obj.cells[0].morphology


def test_validation():
    validate_morphology(morph_obj.segments)

    a= deepcopy(morph_obj)
    a.segments[1].parent=None
    with raises(ValidationException, match='Two segments with parent id as '
                                           '-1'):
        validate_morphology(a.segments)

    b = deepcopy(morph_obj)
    b.segments[0].distal.x = 12
    with raises(ValidationException, match='not connected!!'):
        validate_morphology(b.segments)


def test_load_morph_cells():
    with raises(ValueError, match='The cell id you specified'):
        load_morph_from_cells(nml_obj.cells, cell_id='foo')


def test_tuple():
    points=get_tuple_points(morph_obj.segments)
    assert points==POINTS


