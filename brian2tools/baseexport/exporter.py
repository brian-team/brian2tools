"""
BrianExporter — serialize a Brian2 Network to a portable .brian archive.

The .brian archive is a ZIP file containing:
  - model.json : network structure produced by existing collect_*() functions
                 (same dict as device.runs[0]['components'] in BaseExporter),
                 with Quantity objects converted to JSON-safe dicts
  - arrays.npz : numerical data that cannot go in JSON — state variable values,
                 synaptic connectivity arrays (_synaptic_pre/_synaptic_post)

Call serialize() *after* net.run() to capture both structure and state.

    net.run(10*ms)
    BrianExporter().serialize(net, 'snapshot.brian')

See also
--------
brian2tools.baseimport.importer.BrianImporter
"""

import io
import json
import zipfile

import numpy as np

import brian2
from brian2 import Synapses, get_local_namespace
from brian2.core.variables import ArrayVariable
from brian2.units.fundamentalunits import Quantity

from .collector import (
    collect_EventMonitor,
    collect_NeuronGroup,
    collect_PoissonGroup,
    collect_PoissonInput,
    collect_PopulationRateMonitor,
    collect_SpikeGenerator,
    collect_SpikeMonitor,
    collect_StateMonitor,
    collect_Synapses,
)

# Mirrors collector_map in BaseExporter.network_run() (device.py line 151).
# Tuple: (collector_function, needs_run_namespace)
COLLECTOR_MAP = {
    'neurongroup':           (collect_NeuronGroup, True),
    'poissongroup':          (collect_PoissonGroup, True),
    'spikegeneratorgroup':   (collect_SpikeGenerator, True),
    'statemonitor':          (collect_StateMonitor, False),
    'spikemonitor':          (collect_SpikeMonitor, False),
    'eventmonitor':          (collect_EventMonitor, False),
    'populationratemonitor': (collect_PopulationRateMonitor, False),
    'synapses':              (collect_Synapses, True),
    'poissoninput':          (collect_PoissonInput, True),
}

FORMAT_VERSION = '1'


def _quantity_to_dict(q):
    """
    Convert a Brian2 Quantity to a JSON-serializable dict.

    Stores the raw SI value and the 7-element dimension tuple
    (metre, kg, second, ampere, kelvin, mole, candela exponents)
    from Dimension._dims so reconstruction is unit-system independent.
    """
    value = q.variable if hasattr(q, 'variable') else np.asarray(q)
    return {
        '__type__': 'quantity',
        'value': value.tolist() if isinstance(value, np.ndarray) else float(value),
        'dim': list(q.dim._dims),
    }


def _json_safe(obj, arrays_dict, prefix=''):
    """
    Recursively convert a collector dict to JSON-serializable form.

    The main problem with collector output is that collect_Equations()
    (collector.py line 212) stores eqs.unit as a raw Quantity, and
    collect_PoissonGroup() (line 366), collect_SpikeGenerator() (line 306),
    and _prepare_identifiers() (helper.py line 34) also produce Quantity
    values. This function converts all of them.

    Quantity  → {'__type__': 'quantity', 'value': ..., 'dim': [...]}
    np.ndarray → stored in arrays_dict, replaced by {'__type__': 'array', 'key': ...}
    np.integer / np.floating / np.bool_ → Python primitives
    """
    if isinstance(obj, Quantity):
        return _quantity_to_dict(obj)
    elif isinstance(obj, np.ndarray):
        key = prefix
        arrays_dict[key] = obj
        return {'__type__': 'array', 'key': key}
    elif isinstance(obj, dict):
        return {
            k: _json_safe(v, arrays_dict,
                          prefix=f'{prefix}.{k}' if prefix else k)
            for k, v in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return [
            _json_safe(item, arrays_dict, prefix=f'{prefix}[{i}]')
            for i, item in enumerate(obj)
        ]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


class BrianExporter:
    """
    Export a Brian2 Network to a portable .brian archive after net.run().

    Extends the structural capture of BaseExporter with two things that
    BaseExporter deliberately omits:

    1. State variable values — collect_NeuronGroup() stores equations but
       not the current v[:], w[:] etc. This class captures them.

    2. Actual connectivity arrays — collect_Synapses() (collector.py line 565)
       stores the connect() arguments (condition, p, n) via synapses_connect()
       (device.py line 337), but not the resulting _synaptic_pre/_synaptic_post
       arrays (scalar delays only, line 629). This class captures the arrays
       directly so BrianImporter can restore exact connectivity via
       syn.connect(i=i_arr, j=j_arr) without re-running probabilistic logic.
    """

    def serialize(self, net, filepath, namespace=None, level=0):
        """
        Serialize network structure and state to a .brian archive.

        Parameters
        ----------
        net : brian2.core.network.Network
            A network that has already been run (or at least before_run'd).
        filepath : str
            Destination path; conventionally ends in '.brian'.
        namespace : dict, optional
            Additional namespace for resolving identifiers.  If not given,
            collected from the caller's local scope — same pattern as
            BaseExporter.network_run() (device.py line 141).
        level : int, optional
            Stack depth offset for namespace collection.
        """
        if namespace is None:
            namespace = get_local_namespace(level + 1)

        arrays_dict = {}

        components  = self._collect_structure(net, arrays_dict, namespace)
        state_vars  = self._collect_state(net, arrays_dict)
        connectivity = self._collect_connectivity(net, arrays_dict)

        model = {
            'format_version': FORMAT_VERSION,
            'brian_version': brian2.__version__,
            't': float(net.t_),
            'components': components,
            'state_variables': state_vars,
            'connectivity': connectivity,
        }

        self._write_archive(filepath, model, arrays_dict)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_structure(self, net, arrays_dict, run_namespace):
        """
        Call existing collect_*() functions for every network object.

        Mirrors BaseExporter.network_run() (device.py line 170) using the
        same COLLECTOR_MAP pattern (device.py line 151). Passes result
        through _json_safe() to resolve the Quantity-in-dict problem.

        Also adds 'equations_str' — str(obj.user_equations) — to groups
        that have one, because NeuronGroup.__init__ accepts a plain string
        and str(Equations) produces a canonical parseable form.
        """
        components = {}

        for obj in net.objects:
            obj_type = type(obj).__name__.lower()
            if obj_type not in COLLECTOR_MAP:
                continue

            collector_fn, needs_ns = COLLECTOR_MAP[obj_type]
            obj_dict = (collector_fn(obj, run_namespace)
                        if needs_ns else collector_fn(obj))

            # equations_str lets BrianImporter call NeuronGroup(N, model_str)
            # or Synapses(src, tgt, model_str) directly.
            # NeuronGroup uses user_equations; Synapses uses equations.
            if hasattr(obj, 'user_equations'):
                obj_dict['equations_str'] = str(obj.user_equations)
            elif hasattr(obj, 'equations') and obj.equations is not None:
                obj_dict['equations_str'] = str(obj.equations)

            safe = _json_safe(obj_dict, arrays_dict,
                              prefix=f'struct.{obj_type}.{obj.name}')
            components.setdefault(obj_type, []).append(safe)

        return components

    def _collect_state(self, net, arrays_dict):
        """
        Capture current values of all public ArrayVariables.

        BaseExporter is a Device subclass that intercepts code generation
        before the simulation runs, so it never sees actual values. This
        method runs after net.run() and reads them directly via
        var.get_value() — the same mechanism Network.store() uses internally
        (group.py line 768, VariableOwner._full_state()).
        """
        state_vars = {}
        # Variables internal to Brian2 that should not be serialized.
        _SKIP = frozenset({'i', 'j', 'N', 't', 'dt', 't_in_timesteps'})

        for obj in net.objects:
            if not hasattr(obj, 'variables'):
                continue
            for var_name, var in obj.variables.items():
                if not isinstance(var, ArrayVariable):
                    continue
                # var.owner is a different Python object from obj even when
                # they wrap the same group; compare by name instead of identity.
                if not hasattr(var.owner, 'name'):
                    continue
                if var.owner.name != obj.name:
                    continue
                if var_name.startswith('_') or var_name in _SKIP:
                    continue
                try:
                    values = var.get_value().copy()
                    key = f'state.{obj.name}.{var_name}'
                    arrays_dict[key] = values
                    state_vars[f'{obj.name}.{var_name}'] = {'array_key': key}
                except Exception:
                    pass

        return state_vars

    def _collect_connectivity(self, net, arrays_dict):
        """
        Capture _synaptic_pre and _synaptic_post for every Synapses object.

        collect_Synapses() (collector.py line 565) stores the arguments
        passed to connect() — condition string, p, n — but NOT the resulting
        integer index arrays. For probabilistic connections (p=0.1) or
        condition-based connections, those arguments cannot reproduce the
        exact same connectivity on load. Storing the arrays directly makes
        restoration deterministic.
        """
        connectivity = {}

        for obj in net.objects:
            if not isinstance(obj, Synapses):
                continue
            try:
                i_arr = obj.variables['_synaptic_pre'].get_value().copy()
                j_arr = obj.variables['_synaptic_post'].get_value().copy()
                i_key = f'conn.{obj.name}.i'
                j_key = f'conn.{obj.name}.j'
                arrays_dict[i_key] = i_arr
                arrays_dict[j_key] = j_arr
                connectivity[obj.name] = {'i_key': i_key, 'j_key': j_key}
            except Exception:
                pass

        return connectivity

    def _write_archive(self, filepath, model, arrays_dict):
        """Write model.json + arrays.npz into a single ZIP archive."""
        npz_buf = io.BytesIO()
        np.savez_compressed(npz_buf, **arrays_dict)
        npz_buf.seek(0)

        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('model.json', json.dumps(model, indent=2))
            zf.writestr('arrays.npz', npz_buf.read())
