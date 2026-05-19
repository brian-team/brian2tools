"""
BrianExporter / BrianImporter — end-to-end demo.

Demonstrates the core round-trip:
  1. Build and run a small LIF network.
  2. Serialize to a .brian archive with BrianExporter.
  3. Load it back with BrianImporter and verify state is preserved.

Run:
    python examples/poc_exporter_demo.py
"""

import json
import os
import zipfile

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from brian2 import (
    Network,
    NeuronGroup,
    Synapses,
    StateMonitor,
    SpikeMonitor,
    start_scope,
    ms,
    mV,
)

from brian2tools.baseexport.exporter import BrianExporter
from brian2tools.baseimport import BrianImporter

ARCHIVE = '/tmp/poc_demo.brian'


# ---------------------------------------------------------------------------
# 1. Build and run
# ---------------------------------------------------------------------------

start_scope()

tau = 10 * ms

G = NeuronGroup(
    20,
    'dv/dt = (1 - v) / tau : 1',
    threshold='v > 0.9',
    reset='v = 0',
    method='exact',
    name='neurons',
)
G.v = 'rand()'

S = Synapses(G, G, 'w : 1', on_pre='v += w', name='synapses')
S.connect(j='i')          # one-to-one — deterministic, easy to verify
S.w = '0.05'

mon = StateMonitor(G, 'v', record=True, name='voltage_mon')

net = Network(G, S, mon)
net.run(5 * ms)

print(f'[1] Network ran for {net.t / ms:.1f} ms')
print(f'    G.v[:5]  = {G.v[:5]}')
print(f'    S.w[:5]  = {S.w[:5]}')
print(f'    N_syn    = {len(S.i)}')

# ---------------------------------------------------------------------------
# 2. Serialize
# ---------------------------------------------------------------------------

BrianExporter().serialize(net, ARCHIVE)
print(f'\n[2] Serialized to {ARCHIVE}')

# Show what is inside the archive
with zipfile.ZipFile(ARCHIVE) as zf:
    model = json.loads(zf.read('model.json').decode())
    arrays = dict(np.load(__import__('io').BytesIO(zf.read('arrays.npz')),
                          allow_pickle=False))

print(f'    components : {list(model["components"].keys())}')
print(f'    arrays     : {len(arrays)} entries')
print(f'    network t  : {model["t"] * 1000:.1f} ms')

ng_dict = model['components']['neurongroup'][0]
print(f'    equations_str snippet : {ng_dict["equations_str"].strip()[:60]}')

conn = model['connectivity'].get('synapses', {})
if conn:
    print(f'    connectivity i[:5] : {arrays[conn["i_key"]][:5]}')

# ---------------------------------------------------------------------------
# 3. Reconstruct and verify
# ---------------------------------------------------------------------------

net2, namespace = BrianImporter().load(ARCHIVE)

G2 = next(o for o in net2.objects if o.name == 'neurons')
S2 = next(o for o in net2.objects if o.name == 'synapses')

print(f'\n[3] Reconstructed network')
print(f'    G2.v[:5] = {G2.v[:5]}')
print(f'    S2.w[:5] = {S2.w[:5]}')

# Verify state is identical
assert_allclose(G2.v[:], G.v[:], err_msg='v mismatch after round-trip')
assert_array_equal(S2.i[:], S.i[:])
assert_array_equal(S2.j[:], S.j[:])
assert_allclose(S2.w[:], S.w[:])
assert net2.t_ == net.t_

print('\n[OK] All assertions passed — round-trip is lossless.')

# Clean up
os.unlink(ARCHIVE)
