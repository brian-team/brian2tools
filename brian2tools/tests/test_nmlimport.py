from copy import deepcopy
from neuroml.loaders import NeuroMLLoader
from brian2.units import *
from brian2tools.nmlimport.nml import NmlMorphology,validate_morphology,  \
                                                    ValidationException
from os.path import abspath, dirname,join
from numpy.testing import assert_equal, assert_allclose
from pytest import raises

POINTS = ((0, 'soma', 0.0, 0.0, 0.0, 23.0, -1),
          (1, 'soma', 0.0, 17.0, 0.0, 23.0, 0),
          (2, 'unknown', 0.0, 77.0, 0.0, 6.0, 1),
          (3, 'unknown', 0.0, 477.0, 0.0, 4.4, 2),
          (4, 'unknown', 0.0, 877.0, 0.0, 2.9, 3),
          (5, 'unknown', 0.0, 1127.0, 0.0, 2.0, 4),
          (6, 'unknown', -150.0, 77.0, 0.0, 3.0, 2),
          (7, 'unknown', 0.0, -50.0, 0.0, 4.0, 1),
          (8, 'unknown', 106.07, -156.07, 0.0, 5.0, 7),
          (9, 'unknown', -106.07, -156.07, 0.0, 5.0, 7))

SAMPLE = "samples/sample1.cell.nml"


def get_nml_file(file):
    return NeuroMLLoader.load(abspath(file))


nml_obj = get_nml_file(join(dirname(abspath(__file__)), SAMPLE))
morph_obj = nml_obj.cells[0].morphology


def test_validation():
    validate_morphology(morph_obj.segments)
    a = deepcopy(morph_obj)
    a.segments[1].parent = None
    with raises(ValidationException, match='Two segments with parent id as '
                                           '-1'):
        validate_morphology(a.segments)

    b = deepcopy(morph_obj)
    b.segments[0].distal.x = 12
    with raises(ValidationException, match='not connected!!'):
        validate_morphology(b.segments)


def test_resolved_group_ids():
    nml_object = NmlMorphology(join(dirname(abspath(__file__)), SAMPLE))
    assert_equal(nml_object.resolved_grp_ids['dendrite_group'],
                 [1, 2, 3, 4, 5, 6, 7, 8])

def test_section_child_segment_list():
    nml_object = NmlMorphology(join(dirname(abspath(__file__)), SAMPLE))
    assert_equal([x.id for x in nml_object.section.sectionList[0].sectionList[
        0].segmentList],[2, 3, 4])

def test_load_morphology():
    nml_object = NmlMorphology(join(dirname(abspath(__file__)), SAMPLE))
    morphology=nml_object.morphology_obj
    assert_allclose(morphology.distance, [8.5] * um)
    assert_allclose(morphology.length, [17.] * um)
    assert_allclose(morphology.coordinates, [[0., 0., 0.], [0., 17., 0.]] * um)
    assert_allclose(morphology.area, [1228.36272755] * um2)

