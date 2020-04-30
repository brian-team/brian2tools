import tempfile
from subprocess import call

import matplotlib.pyplot as plt
import numpy as np
from numpy.testing import assert_allclose, assert_equal
from pytest import mark, raises
# We avoid "from brian2 import *", as this would also import Brian's test
# function which will then be collected by py.test
from brian2 import set_device, NeuronGroup, StateMonitor, SpikeMonitor, run
from brian2 import second, mV, amp, metre, psiemens, ms

from brian2tools.nmlexport.supporting import *
from brian2tools.nmlutils.utils import from_string

plain_numbers_from_list = lambda x: str(x)[1:-1].replace(',','')

RECORDING_BRIAN_FILENAME = "recording"
LEMS_OUTPUT_FILENAME     = "ifcgmtest.xml"

# We assume that JNML_HOME has been set
JNML_PATH = os.environ.get('JNML_HOME', None)

xml_filename = "ifcgmtest.xml"
idx_to_record = [2, 55, 98]
output_jnml_file = "recording_ifcgmtest"


def simulation1(flag_device=False, path="", rec_idx=idx_to_record):
    if flag_device:
        set_device('neuroml2', filename=LEMS_OUTPUT_FILENAME)
    n = 100
    duration = 1*second
    tau = 10*ms

    eqs = '''
    dv/dt = (v0 - v) / tau : volt (unless refractory)
    v0 : volt
    '''
    group = NeuronGroup(n, eqs, threshold='v > 10*mV', reset='v = 0*mV',
                        refractory=5*ms, method='linear')
    group.v = 0*mV
    group.v0 = '20*mV * i / (N-1)'

    statemonitor = StateMonitor(group, 'v', record=rec_idx)
    spikemonitor = SpikeMonitor(group, record=rec_idx)
    run(duration)

    if not flag_device:
        recvec = []
        for ri in rec_idx:
            recvec.append(statemonitor[ri].v)
        recvec = np.asarray(recvec)
        return recvec
    else:
        return None

@mark.skipif(JNML_PATH is None,
             reason='Cannot run jnml, set the JNML_HOME environment variable')
def test_simulation1(plot=False):
    """
    Test example 1: simulation1_lif.py
    """

    current_path = os.getcwd()
    tempdir = tempfile.mkdtemp()
    outbrian = simulation1(False, path=tempdir)
    outnml = simulation1(True, path=tempdir)
    set_device('runtime')
    os.chdir(JNML_PATH)
    outcommand = call("jnml {path} -nogui".format(path=os.path.join(current_path, xml_filename)),
                      shell=True)

    timevec = []
    valuesvec = []
    with open(output_jnml_file+'.dat','r') as f:
        for line in f:
            timevec.append(float(line.split("\t")[0]))
            valuesvec.append([float(x) for x in line.split("\t")[1:-1]])

    timevec = np.asarray(timevec)
    valuesvec = np.asarray(valuesvec).T
    for i in range(len(idx_to_record)):
        assert_allclose(outbrian[i, :], valuesvec[i, 1:], atol=1e-02)

    if plot:
        plt.subplot(3,2,1)
        plt.plot(outbrian[0,:])
        plt.subplot(3,2,2)
        plt.plot(valuesvec[0,:])
        plt.subplot(3,2,3)
        plt.plot(outbrian[1,:])
        plt.subplot(3,2,4)
        plt.plot(valuesvec[1,:])
        plt.subplot(3,2,5)
        plt.plot(outbrian[2,:])
        plt.subplot(3,2,6)
        plt.plot(valuesvec[2,:])
        plt.show()
    os.chdir(current_path)

simplenetwork_tag_output = '''<network id="net">
  <Component a="3" b="4" id="i0" type="lf"/>
</network>
'''


def test_units_parser():
    testlist = ["1 mV", "1.234mV", "1.2e-4 mV", "1.23e-5A", "1.23e4A",
                "1.45E-8 m", "1.23E-8m2", "60", "6000", "123000",
                "-1.00000008E8", "0.07 per_ms", "10pS"]
    reslist = [ 1*mV, 1.234*mV, 1.2e-4*mV, 1.23e-5*amp, 1.23e4*amp,
                1.45e-8*metre, 1.23e-8*metre**2, 60, 6000, 123000,
                -1.00000008e8, 0.07/ms, 10*psiemens]
    for t, r in zip(testlist, reslist):
        assert_equal(r, from_string(t))


def test_brian_unit_to_lems():
    assert_equal(brian_unit_to_lems(20.*mV), "20.*mV")
    assert_equal(brian_unit_to_lems(0*ms), "0")


def test_neuromlsimulation():
    nmlsim = NeuroMLSimulation('a', 'b')
    with raises(AssertionError):
        nmlsim.add_line('line1', 'v')
    nmlsim.add_display('ex')
    nmlsim.add_line('line1', 'v')
    nmlsim.add_line('line2', 'w')
    with raises(AssertionError):
        nmlsim.add_outputcolumn('1', '[3]')
    nmlsim.add_outputfile('of1')
    nmlsim.add_outputcolumn('1', '[3]')
    with raises(AssertionError):
        nmlsim.add_eventselection('1', '[5]')
    nmlsim.add_eventoutputfile('eof1')
    nmlsim.add_eventselection('1', '[5]')
    xml = nmlsim.build()

    # Simulation
    assert xml.tagName == 'Simulation'
    for k, v in [('id', 'a'), ('length', '1s'), ('step', '0.1ms'), ('target', 'b')]:
        assert xml.getAttributeNode(k).value == v
    children = xml.childNodes
    assert len(children) == 3
    # Display
    display = children[0]
    assert display.tagName == 'Display'
    for k, v in [("id", "ex"), ("timeScale", "1ms"), ("title", ""), ("xmax", "1000"), ("xmin", "0"),
                 ("ymax", "11"), ("ymin", "0")]:
        assert display.getAttributeNode(k).value == v
    lines = display.childNodes
    assert len(lines) == 2
    for name, q, line in [('line1', 'v', lines[0]),
                          ('line2', 'w', lines[1])]:
        assert line.tagName == 'Line'
        for k, v in [("id", name), ("quantity", q), ("scale", "1mV"), ("timeScale", "1ms")]:
            assert line.getAttributeNode(k).value == v
    # OutputFile
    output_file = children[1]
    assert output_file.tagName == 'OutputFile'
    for k, v in [("id", "of1"), ("fileName", "recordings.dat")]:
        assert output_file.getAttributeNode(k).value == v
    assert len(output_file.childNodes) == 1
    output_column = output_file.childNodes[0]
    assert output_column.tagName == "OutputColumn"
    for k, v in [("id", "1"), ("quantity", "[3]")]:
        assert output_column.getAttributeNode(k).value == v
    # EventOutputFile
    event_output = children[2]
    assert event_output.tagName == 'EventOutputFile'
    for k, v in [("id", "eof1"), ("fileName", "recordings.spikes"), ("format", "TIME_ID")]:
        assert event_output.getAttributeNode(k).value == v
    assert len(event_output.childNodes) == 1
    event_selection = event_output.childNodes[0]
    assert event_selection.tagName == 'EventSelection'
    for k, v in [("id", "1"), ("select", "[5]"), ("eventPort", "spike")]:
        assert event_selection.getAttributeNode(k).value == v


def test_simplenetwork():
    nmlnet = NeuroMLSimpleNetwork("net")
    nmlnet.add_component("i0", "lf", a=3, b=4)
    xml = nmlnet.build()
    assert xml.tagName == 'network'
    assert xml.getAttributeNode('id').value == 'net'
    children = xml.childNodes
    assert len(children) == 1
    child = children[0]
    assert child.tagName == 'Component'
    for k, v in [('a', "3"), ('b', "4"), ('id', "i0"), ('type', "lf")]:
        assert child.getAttributeNode(k).value == v
