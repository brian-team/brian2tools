# PoC: BrianExporter / BrianImporter

Proof-of-concept for GSoC 2026: *Serialization/Deserialization for Brian2 models, results, and input data*.

## What this is

A minimal demonstration that a Brian2 network — equations, connectivity, and state variables — can be serialized to a portable archive and reconstructed object-by-object without running the simulation again.

This PoC lives entirely in `brian2tools` and builds on the existing `collect_*()` infrastructure in `brian2tools/baseexport/collector.py`.

## What was built

```
brian2tools/baseexport/exporter.py   BrianExporter.serialize(net, 'file.brian')
brian2tools/baseimport/__init__.py   package entry point
brian2tools/baseimport/importer.py   BrianImporter.load('file.brian') → (net, namespace)
brian2tools/tests/test_poc_exporter.py   11 tests covering archive structure + round-trips
examples/poc_exporter_demo.py        end-to-end demo
```

The `.brian` archive is a ZIP file containing:
- `model.json` — network structure from existing `collect_*()` functions, with `Quantity` objects converted to JSON-safe dicts
- `arrays.npz` — numerical data: state variable values + synaptic connectivity arrays

## How to run

```bash
# Install brian2tools in development mode (from repo root)
pip install -e .

# Run the demo
python examples/poc_exporter_demo.py

# Run the tests
python -m pytest brian2tools/tests/test_poc_exporter.py -v
```

## Core mechanism

`BrianExporter.serialize()` does three things that `BaseExporter` deliberately omits:

1. **Converts Quantities to JSON** — `collect_Equations()` stores `eqs.unit` as a raw `Quantity`; `_json_safe()` converts all Quantities to `{'__type__': 'quantity', 'value': ..., 'dim': [7-element SI exponent tuple]}`.

2. **Captures state variable values** — `BaseExporter` intercepts code generation before the simulation, so it never sees actual values. `_collect_state()` reads them after `net.run()` via `var.get_value()`.

3. **Captures actual connectivity arrays** — `collect_Synapses()` stores the `connect()` arguments (condition, p, n) but not the resulting `_synaptic_pre`/`_synaptic_post` arrays. `_collect_connectivity()` captures the arrays directly so `BrianImporter` can restore exact connectivity via `syn.connect(i=i_arr, j=j_arr)` — critical for probabilistic connections.

`BrianImporter.load()` reconstructs objects in dependency order (groups → synapses → state restore) and returns a `Network` ready to continue running.

## What this is not

- Not a full implementation — monitors, PoissonGroup, SpikeGeneratorGroup, and SpatialNeuron reconstruction are planned but not in this PoC.
- Not a device mode integration — `BrianExporter` is called explicitly after `net.run()`, not via `set_device('exporter')`.
- Not production-ready — edge cases (TimedArray identifiers, multiple clocks, SpatialNeuron) are out of scope for this PoC.
