from copy import deepcopy
from os.path import abspath, dirname, join

from neuroml.loaders import NeuroMLLoader
from brian2.units import *
from numpy.testing import assert_equal, assert_allclose
from pytest import raises

from brian2tools.nmlimport.nml import NMLMorphology, validate_morphology, \
    ValidationException
from brian2tools.nmlutils.utils import string_to_quantity

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


def test_resolved_group_ids():
    nml_object = NMLMorphology(join(dirname(abspath(__file__)), SAMPLE))
    assert_equal(nml_object.segment_groups['dendrite_group'],
                 [1, 2, 3, 4, 5, 6, 7, 8])


def test_section_child_segment_list():
    nml_object = NMLMorphology(join(dirname(abspath(__file__)), SAMPLE))
    assert_equal([x.id for x in nml_object.section.sectionList[0].sectionList[
        0].segmentList], [2, 3, 4])


def test_load_morphology():
    nml_object = NMLMorphology(join(dirname(abspath(__file__)), SAMPLE))
    morphology = nml_object.morphology
    assert_allclose(morphology.distance, [8.5] * um)
    assert_allclose(morphology.length, [17.] * um)
    assert_allclose(morphology.coordinates, [[0., 0., 0.], [0., 17., 0.]] * um)
    assert_allclose(morphology.area, [1228.36272755] * um2)


def test_string_to_quantities():
    testlist = ["1 mV", "1.234mV", "1.2e-4 mV", "1.23e-5A", "1.23e4A",
                "1.45E-8 m", "1.23E-8m2", "60", "0.2 kohm_cm", "1.28e3per_s",
                "-1.00000008E8", "0.07 per_ms", "10pS"]
    reslist = [1 * mV, 1.234 * mV, 1.2e-4 * mV, 1.23e-5 * amp, 1.23e4 * amp,
               1.45e-8 * metre, 1.23e-8 * metre ** 2, 60, 0.2 * kohm * cmetre,
               1.28 * kHz, -1.00000008e8, 0.07 / ms, 10 * psiemens]
    for t, r in zip(testlist, reslist):
        assert_equal(r, string_to_quantity(t))


def test_get_properties():
    nml_object = NMLMorphology(join(dirname(abspath(__file__)), SAMPLE))
    d = {'threshold': 'v > 0*mV', 'refractory': 'v > 0*mV',
         'Cm': string_to_quantity("2.84 uF_per_cm2"),
         'Ri': string_to_quantity("0.2 kohm_cm")}
    assert_equal(set(nml_object.properties.keys()), set(d.keys()))
    assert_equal(nml_object.properties['Cm'], d['Cm'])
    assert_equal(nml_object.properties['Ri'], d['Ri'])
    for key in ['threshold', 'refractory']:
        value = nml_object.properties[key]
        components = value.split('>')
        assert len(components) == 2
        assert components[0].strip() == 'v'
        # Compare the strings as quantities (e.g. 0*mV == 0.*volt)
        assert_equal(eval(components[1].strip()), eval(d[key].split('>')[1]))


def test_channel_properties():
    nml_object = NMLMorphology(join(dirname(abspath(__file__)), SAMPLE))

    channel_properties = nml_object.channel_properties
    print(channel_properties)
    assert set(channel_properties.keys()) == {'soma_group', 'all'}
    assert set(channel_properties['soma_group'].keys()) == {'g_Ca_pyr', 'E_Ca_pyr',
                                                            'g_Kahp_pyr', 'E_Kahp_pyr',
                                                            'g_Na_pyr', 'E_Na_pyr',
                                                            'g_Kdr_pyr', 'E_Kdr_pyr'}
    assert set(channel_properties['all'].keys()) == {'g_LeakConductance_pyr', 'E_LeakConductance_pyr'}

    # Check a few values
    assert channel_properties['soma_group']['g_Ca_pyr'] == 10. * msiemens / cm2
    assert channel_properties['soma_group']['E_Ca_pyr'] == 80. * mvolt
    assert channel_properties['soma_group']['g_Kahp_pyr'] == 25. * siemens / meter ** 2
    assert channel_properties['soma_group']['E_Kahp_pyr'] == -75. * mvolt
