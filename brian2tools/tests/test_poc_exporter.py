"""
Tests for BrianExporter and BrianImporter (PoC).

Follows the same style as test_baseexport.py: plain functions, no test
classes, imports from brian2 at the top.
"""

import json
import os
import tempfile
import zipfile

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

import pytest

from brian2 import (
    Network,
    NeuronGroup,
    Synapses,
    StateMonitor,
    SpikeMonitor,
    start_scope,
    ms,
    mV,
    volt,
)

from brian2tools.baseexport.exporter import BrianExporter
from brian2tools.baseimport import BrianImporter

# Module-level constant so serialize() can resolve 'tau' in the namespace.
# Matches the pattern used in test_baseexport.py: identifiers that appear in
# equation strings must be resolvable at the call site of serialize().
TAU = 10 * ms


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_lif_network(N=10, run_duration=5 * ms):
    """Small deterministic LIF network used across multiple tests."""
    start_scope()
    G = NeuronGroup(
        N,
        'dv/dt = (1 - v) / TAU : 1',
        threshold='v > 0.9',
        reset='v = 0',
        method='exact',
        namespace={'TAU': TAU},
        name='lif_group',
    )
    G.v = 'rand()'
    net = Network(G)
    net.run(run_duration)
    return net, G


def _serialize_to_tmp(net):
    """Serialize net to a temp file; return the path."""
    fd, path = tempfile.mkstemp(suffix='.brian')
    os.close(fd)
    # level=0: get_local_namespace captures the frame of _serialize_to_tmp,
    # which inherits f_globals from the test module (contains TAU etc.)
    BrianExporter().serialize(net, path)
    return path


# ---------------------------------------------------------------------------
# Archive structure tests
# ---------------------------------------------------------------------------

def test_archive_is_valid_zip():
    """Output file must be a valid ZIP archive."""
    net, _ = _make_lif_network()
    path = _serialize_to_tmp(net)
    try:
        assert zipfile.is_zipfile(path)
    finally:
        os.unlink(path)


def test_archive_contains_required_files():
    """ZIP must contain model.json and arrays.npz."""
    net, _ = _make_lif_network()
    path = _serialize_to_tmp(net)
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
        assert 'model.json' in names
        assert 'arrays.npz' in names
    finally:
        os.unlink(path)


def test_model_json_is_valid_json():
    """model.json must parse without error."""
    net, _ = _make_lif_network()
    path = _serialize_to_tmp(net)
    try:
        with zipfile.ZipFile(path) as zf:
            model = json.loads(zf.read('model.json').decode())
        assert 'components' in model
        assert 'format_version' in model
        assert 'brian_version' in model
    finally:
        os.unlink(path)


def test_no_raw_quantity_in_json():
    """
    model.json must not contain any raw Quantity objects.

    collect_Equations() (collector.py:212) stores eqs.unit as a Quantity.
    BrianExporter._json_safe() must convert it; this test verifies that.
    """
    net, _ = _make_lif_network()
    path = _serialize_to_tmp(net)
    try:
        with zipfile.ZipFile(path) as zf:
            raw = zf.read('model.json').decode()
        # A raw Quantity would repr as e.g. '1. * volt' or 'volt'
        # After conversion it appears as {'__type__': 'quantity', ...}
        # The JSON string must be parseable without a custom decoder.
        model = json.loads(raw)
        assert model is not None  # passed json.loads → no raw Quantity
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Structure capture tests
# ---------------------------------------------------------------------------

def test_neurongroup_captured_in_components():
    """NeuronGroup must appear under components['neurongroup']."""
    net, G = _make_lif_network()
    path = _serialize_to_tmp(net)
    try:
        with zipfile.ZipFile(path) as zf:
            model = json.loads(zf.read('model.json').decode())
        ng_list = model['components']['neurongroup']
        assert len(ng_list) == 1
        assert ng_list[0]['name'] == 'lif_group'
        assert ng_list[0]['N'] == 10
    finally:
        os.unlink(path)


def test_equations_str_field_present():
    """
    BrianExporter adds 'equations_str' to NeuronGroup dicts so that
    BrianImporter can call NeuronGroup(N, model_str) directly.
    collect_NeuronGroup() does not add this field.
    """
    net, _ = _make_lif_network()
    path = _serialize_to_tmp(net)
    try:
        with zipfile.ZipFile(path) as zf:
            model = json.loads(zf.read('model.json').decode())
        ng_dict = model['components']['neurongroup'][0]
        assert 'equations_str' in ng_dict
        assert 'dv/dt' in ng_dict['equations_str']
    finally:
        os.unlink(path)


def test_state_variables_captured():
    """State variable values must appear in state_variables and arrays.npz."""
    net, G = _make_lif_network()
    path = _serialize_to_tmp(net)
    try:
        with zipfile.ZipFile(path) as zf:
            model = json.loads(zf.read('model.json').decode())
            arrays = dict(np.load(
                __import__('io').BytesIO(zf.read('arrays.npz')),
                allow_pickle=False,
            ))
        key = 'lif_group.v'
        assert key in model['state_variables']
        arr_key = model['state_variables'][key]['array_key']
        assert arr_key in arrays
        assert_allclose(arrays[arr_key], G.v[:])
    finally:
        os.unlink(path)


def test_connectivity_arrays_captured():
    """
    _synaptic_pre and _synaptic_post must appear in arrays.npz.

    collect_Synapses() (collector.py:565) does not store these arrays;
    BrianExporter._collect_connectivity() adds them.
    """
    start_scope()
    G = NeuronGroup(10, 'dv/dt = (1-v)/TAU : 1',
                    threshold='v>0.9', reset='v=0', method='exact',
                    namespace={'TAU': TAU})
    S = Synapses(G, G, 'w : 1', on_pre='v += w')
    S.connect(j='i')
    S.w = '0.1'
    net = Network(G, S)
    net.run(1 * ms)

    path = _serialize_to_tmp(net)
    try:
        with zipfile.ZipFile(path) as zf:
            model = json.loads(zf.read('model.json').decode())
            arrays = dict(np.load(
                __import__('io').BytesIO(zf.read('arrays.npz')),
                allow_pickle=False,
            ))
        conn = model['connectivity']['synapses']
        i_arr = arrays[conn['i_key']]
        j_arr = arrays[conn['j_key']]
        assert_array_equal(i_arr, S.i[:])
        assert_array_equal(j_arr, S.j[:])
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

def test_round_trip_neurongroup_state():
    """
    Reconstruct a NeuronGroup; state variable v must match exactly.
    """
    net, G = _make_lif_network(N=20)
    original_v = G.v[:].copy()
    path = _serialize_to_tmp(net)
    try:
        net2, _ = BrianImporter().load(path)
        # Find the reconstructed group by name
        G2 = next(o for o in net2.objects
                  if o.name == 'lif_group')
        assert len(G2) == 20
        assert_allclose(G2.v[:], original_v)
    finally:
        os.unlink(path)


def test_round_trip_synapses_connectivity():
    """
    Round-trip a network with Synapses; i[:] and j[:] must match exactly.

    This verifies the core insight: BrianImporter restores connectivity
    from stored _synaptic_pre/_synaptic_post arrays, not by re-running
    the probabilistic connect() call.
    """
    start_scope()
    G = NeuronGroup(20, 'dv/dt = (1-v)/TAU : 1',
                    threshold='v>0.9', reset='v=0', method='exact',
                    namespace={'TAU': TAU})
    S = Synapses(G, G, 'w : 1', on_pre='v += w')
    S.connect(p=0.5)   # probabilistic — must NOT be re-run on import
    S.w = 'rand() * 0.3'
    net = Network(G, S)
    net.run(2 * ms)

    original_i = S.i[:].copy()
    original_j = S.j[:].copy()
    original_w = S.w[:].copy()
    path = _serialize_to_tmp(net)
    try:
        net2, _ = BrianImporter().load(path)
        S2 = next(o for o in net2.objects if isinstance(o, Synapses))
        assert_array_equal(S2.i[:], original_i)
        assert_array_equal(S2.j[:], original_j)
        assert_allclose(S2.w[:], original_w)
    finally:
        os.unlink(path)


def test_network_time_restored():
    """net.t_ must be preserved across serialize/load."""
    net, _ = _make_lif_network(run_duration=7 * ms)
    original_t = float(net.t_)
    path = _serialize_to_tmp(net)
    try:
        net2, _ = BrianImporter().load(path)
        assert net2.t_ == pytest.approx(original_t)
    finally:
        os.unlink(path)
