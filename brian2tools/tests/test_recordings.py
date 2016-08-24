import unittest
import os
import sys
import platform
import tempfile
import numpy as np
from subprocess import call
from brian2 import *
from brian2tools.nmlexport import *
import matplotlib.pyplot as plt

from numpy.testing import assert_raises, assert_equal, assert_array_equal

plain_numbers_from_list = lambda x: str(x)[1:-1].replace(',','')

plot = False
RECORDING_BRIAN_FILENAME = "recording"
LEMS_OUTPUT_FILENAME     = "ifcgmtest.xml"

if platform.system()=='Windows':
    JNML_PATH = "C:/jNeuroMLJar"
else:
    JNML_PATH = ""
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

def test_simulation1():
    """
    Test example 1: simulation1_lif.py
    """

    current_path = os.getcwd()
    tempdir = tempfile.mkdtemp()
    outbrian = simulation1(False, path=tempdir)
    outnml = simulation1(True, path=tempdir)

    if JNML_PATH:
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
        assert np.allclose(outbrian[i, :], valuesvec[i, 1:], atol=1e-02)==True

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
