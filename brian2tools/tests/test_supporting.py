import os
import sys
sys.path.append(os.path.dirname(os.getcwd()))
from brian2 import *
from brian2tools.nmlexport import *
from brian2tools.nmlexport.supporting import *

from numpy.testing import assert_raises, assert_equal, assert_array_equal

simulation_tag_output = '''<Simulation id="a" length="1s" step="0.1ms" target="b">
  <Display id="ex" timeScale="1ms" title="" xmax="1000" xmin="0" ymax="11" ymin="0">
    <Line id="line1" quantity="v" scale="1mV" timeScale="1ms"/>
    <Line id="line2" quantity="w" scale="1mV" timeScale="1ms"/>
  </Display>
  <OutputFile fileName="recordings.dat" id="of1">
    <OutputColumn id="1" quantity="[3]"/>
  </OutputFile>
  <EventOutputFile fileName="recordings.spikes" format="TIME_ID" id="eof1">
    <EventSelection eventPort="spike" id="1" select="[5]"/>
  </EventOutputFile>
</Simulation>
'''

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
    assert_raises(AssertionError, lambda: nmlsim.add_line('line1', 'v'))
    nmlsim.add_display('ex')
    nmlsim.add_line('line1', 'v')
    nmlsim.add_line('line2', 'w')
    assert_raises(AssertionError, lambda: nmlsim.add_outputcolumn('1', '[3]'))
    nmlsim.add_outputfile('of1')
    nmlsim.add_outputcolumn('1', '[3]')
    assert_raises(AssertionError, lambda: nmlsim.add_eventselection('1', '[5]'))
    nmlsim.add_eventoutputfile('eof1')
    nmlsim.add_eventselection('1', '[5]')
    nmlsim.build()
    strrepr = nmlsim.__repr__()
    assert_equal(strrepr, simulation_tag_output)

def test_simplenetwork():
    nmlnet = NeuroMLSimpleNetwork("net")
    nmlnet.add_component("i0", "lf", a=3, b=4)
    nmlnet.build()
    strrepr = nmlnet.__repr__()
    assert_equal(strrepr, simplenetwork_tag_output)
