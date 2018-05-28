from copy import deepcopy
from neuroml.loaders import NeuroMLLoader
from brian2.units import *
from brian2tools.nmlimport.nml import load_morphology,get_tuple_points,\
    validate_morphology,load_morph_from_cells,ValidationException
from os.path import abspath
from numpy.testing import assert_equal
from pytest import raises

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


def get_nml_file(file):
    return NeuroMLLoader.load(abspath((file)))


nml_obj= get_nml_file("samples/sample1.cell.nml")
# nml_obj= get_nml_file("samples/sample2.nml")
morph_obj= nml_obj.cells[0].morphology


def test_validation():
    print("sg")
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
    assert_equal(points,POINTS)


def test_load_morphology():
    morphology = load_morphology("samples/sample1.cell.nml")
    assert_equal(morphology.distance,[ 8.5]*um)
    assert_equal(morphology.length,[ 17.]*um)
    assert_equal(morphology.coordinates,[[0.,0.,0.],[0.,17.,0.]]*um)

    assert_equal(morphology.area,[1228.36272755]*um2)
    area = Quantity.with_dimensions([1228.36272755e-12], length=2)
    print(Quantity.has_same_dimensions(morphology.area, area))
    assert_equal(morphology.area,area)