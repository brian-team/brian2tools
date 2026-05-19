"""
BrianImporter — reconstruct a Brian2 Network from a .brian archive.

The importer reads the model.json + arrays.npz produced by BrianExporter
and calls the standard Brian2 constructors to recreate each object.

Each _reconstruct_*() method maps directly from the dict fields produced
by the corresponding collect_*() function in collector.py, augmented by
the extra fields BrianExporter adds (equations_str, state_variables,
connectivity arrays).

This is a minimal implementation covering NeuronGroup and Synapses — enough
to demonstrate that the round-trip approach is sound.  Monitors, PoissonGroup,
SpikeGeneratorGroup follow the same pattern and will be added in the full
implementation.
"""

import io
import json
import warnings
import zipfile

import numpy as np

import brian2
from brian2 import Network, NeuronGroup, Synapses, ms, second
from brian2.core.variables import ArrayVariable, DynamicArrayVariable
from brian2.units.fundamentalunits import Dimension, Quantity


def _dict_to_quantity(d):
    """
    Inverse of _quantity_to_dict() in exporter.py.

    Reconstructs a Quantity from {'value': ..., 'dim': [7 floats]}.

    Directly constructs a Dimension from the stored 7-element _dims tuple
    (metre, kg, second, amp, kelvin, mole, candela exponents).  This avoids
    depending on a specific unit name being exported and is robust across
    Brian2 versions since _dims is a stable internal attribute.
    """
    value = np.asarray(d['value'])
    dims_tuple = tuple(float(x) for x in d['dim'])
    dim = Dimension.__new__(Dimension)
    object.__setattr__(dim, '_dims', dims_tuple)
    return Quantity(value, dim=dim)


def _restore_obj(obj_dict):
    """
    Walk a JSON-safe dict and convert {'__type__': 'quantity', ...} entries
    back to Quantity objects, and {'__type__': 'array', ...} entries to a
    sentinel (arrays are loaded separately from arrays.npz).
    """
    if isinstance(obj_dict, dict):
        if obj_dict.get('__type__') == 'quantity':
            return _dict_to_quantity(obj_dict)
        return {k: _restore_obj(v) for k, v in obj_dict.items()}
    elif isinstance(obj_dict, list):
        return [_restore_obj(item) for item in obj_dict]
    return obj_dict


class BrianImporter:
    """
    Reconstruct a Brian2 Network from a .brian archive.

    Usage
    -----
    net, namespace = BrianImporter().load('snapshot.brian')
    net.run(10*ms)   # continue from the saved state

    The returned namespace contains any TimedArray or custom-function
    objects that were part of the original network's identifier scope.
    """

    def load(self, filepath):
        """
        Load a .brian archive and return a reconstructed Network.

        Parameters
        ----------
        filepath : str
            Path to a .brian archive created by BrianExporter.

        Returns
        -------
        net : brian2.core.network.Network
        namespace : dict
            Namespace containing reconstructed TimedArray objects and
            any other non-Quantity identifiers from the original network.
        """
        model_dict, arrays = self._load_archive(filepath)
        self._check_version(model_dict)

        components = model_dict.get('components', {})
        state_vars = model_dict.get('state_variables', {})
        connectivity = model_dict.get('connectivity', {})

        namespace = {}
        groups_by_name = {}
        all_objects = []

        # --- NeuronGroups -------------------------------------------------
        # Must be reconstructed before Synapses (source/target resolution).
        for ng_dict in components.get('neurongroup', []):
            ng = self._reconstruct_neurongroup(ng_dict, namespace)
            groups_by_name[ng.name] = ng
            all_objects.append(ng)

        # --- Synapses -----------------------------------------------------
        # After all groups exist; connect() uses stored i/j arrays.
        for syn_dict in components.get('synapses', []):
            syn = self._reconstruct_synapses(
                syn_dict, groups_by_name, connectivity, arrays, namespace
            )
            groups_by_name[syn.name] = syn
            all_objects.append(syn)

        # --- Restore state ------------------------------------------------
        # Done AFTER connect() so DynamicArrayVariable sizes (set by
        # connect()) are correct before we write synaptic variable values.
        # Mirrors VariableOwner._restore_from_full_state() (group.py:780).
        for obj in all_objects:
            self._restore_state(obj, state_vars, arrays)

        net = Network(*all_objects)
        net.t_ = model_dict.get('t', 0.0)
        return net, namespace

    # ------------------------------------------------------------------
    # Reconstruction helpers
    # ------------------------------------------------------------------

    def _reconstruct_neurongroup(self, ng_dict, namespace):
        """
        Reconstruct a NeuronGroup from its serialized dict.

        Consumes collect_NeuronGroup() (collector.py:20) output, augmented
        by BrianExporter's 'equations_str' field.

        Key mappings
        ------------
        ng_dict['N']             ← group._N             (collector.py:47)
        ng_dict['equations_str'] ← str(user_equations)  (added by exporter)
        ng_dict['events']['spike']['threshold']['code']  (collector.py:254)
        ng_dict['events']['spike']['reset']['code']      (collector.py:262)
        ng_dict['events']['spike']['refractory']         (collector.py:269)
        ng_dict['user_method']   ← method_choice        (collector.py:50)
        ng_dict['identifiers']   ← _prepare_identifiers (helper.py:12)
        """
        N = ng_dict['N']
        model_str = ng_dict.get('equations_str', '')
        kwargs = {'name': ng_dict['name']}

        if ng_dict.get('user_method'):
            kwargs['method'] = ng_dict['user_method']

        # Extract threshold / reset / refractory from the events dict
        # produced by collect_Events() (collector.py:225).
        events = _restore_obj(ng_dict.get('events', {}))
        if 'spike' in events:
            spike = events['spike']
            kwargs['threshold'] = spike['threshold']['code']
            if 'reset' in spike:
                kwargs['reset'] = spike['reset']['code']
            if 'refractory' in spike:
                kwargs['refractory'] = spike['refractory']

        # Rebuild namespace from stored identifiers so the equation string
        # can resolve user-defined constants (e.g. tau = 10*ms).
        # _prepare_identifiers() (helper.py:12) filters to Quantity,
        # TimedArray, and custom Function objects only.
        identifiers = _restore_obj(ng_dict.get('identifiers', {}))
        namespace.update(identifiers)

        return NeuronGroup(N, model_str, namespace=namespace, **kwargs)

    def _reconstruct_synapses(self, syn_dict, groups_by_name,
                               connectivity, arrays, namespace):
        """
        Reconstruct a Synapses object and restore connectivity.

        Consumes collect_Synapses() (collector.py:565) output, augmented
        by BrianExporter's 'equations_str' and connectivity arrays.

        Key mappings
        ------------
        syn_dict['source'] ← collect_SpikeSource()   (collector.py:396)
                             str or {'start','stop','group'} for Subgroups
        syn_dict['pathways'][*]['prepost'] / ['code'] (collector.py:619-631)
        connectivity[name]['i_key'], ['j_key']  ← _synaptic_pre/_post arrays
        """
        source = self._resolve_source(syn_dict['source'], groups_by_name)
        target = self._resolve_source(syn_dict['target'], groups_by_name)

        kwargs = {'name': syn_dict['name'], 'namespace': namespace}

        if syn_dict.get('equations_str'):
            kwargs['model'] = syn_dict['equations_str']

        if syn_dict.get('user_method'):
            kwargs['method'] = syn_dict['user_method']

        # Extract on_pre / on_post from the pathways list.
        # collect_Synapses() (collector.py:619) stores each SynapticPathway
        # as {'prepost': 'pre'/'post', 'code': str, ...}.
        for pathway in syn_dict.get('pathways', []):
            if pathway['prepost'] == 'pre':
                kwargs['on_pre'] = pathway['code']
            elif pathway['prepost'] == 'post':
                kwargs['on_post'] = pathway['code']

        syn = Synapses(source, target, **kwargs)

        # Restore connectivity from stored i/j arrays rather than
        # re-running the original condition string.  This is the critical
        # difference from BaseExporter: probabilistic connections (p=0.1)
        # would produce different results each run.
        conn = connectivity.get(syn_dict['name'])
        if conn:
            i_arr = arrays[conn['i_key']]
            j_arr = arrays[conn['j_key']]
            if len(i_arr) > 0:
                syn.connect(i=i_arr, j=j_arr)
        else:
            syn.connect()

        return syn

    def _resolve_source(self, source_ref, groups_by_name):
        """
        Resolve a collect_SpikeSource() return value to a Brian2 group.

        collect_SpikeSource() (collector.py:396) returns:
          str                              → regular group (use name directly)
          {'start': int, 'stop': int,
           'group': str}                  → Subgroup slice
        Note: 'stop' in the dict is inclusive (source.stop - 1 at line 406).
        """
        if isinstance(source_ref, dict):
            parent = groups_by_name[source_ref['group']]
            return parent[source_ref['start']:source_ref['stop'] + 1]
        return groups_by_name[source_ref]

    def _restore_state(self, obj, state_vars, arrays):
        """
        Set state variable values from arrays.npz after construction.

        Called after connect() so DynamicArrayVariable sizes are finalised.
        Mirrors VariableOwner._restore_from_full_state() (brian2 group.py:780):
        resize DynamicArrayVariables before calling set_value().
        """
        if not hasattr(obj, 'variables'):
            return

        for key, info in state_vars.items():
            obj_name, var_name = key.split('.', 1)
            if obj_name != obj.name:
                continue
            if var_name not in obj.variables:
                continue

            var = obj.variables[var_name]
            if not isinstance(var, ArrayVariable) or var.read_only:
                continue

            array_key = info['array_key']
            if array_key not in arrays:
                continue

            values = arrays[array_key]
            try:
                if isinstance(var, DynamicArrayVariable):
                    var.resize(len(values))
                var.set_value(values)
            except Exception as exc:
                warnings.warn(f'Could not restore {key}: {exc}')

    # ------------------------------------------------------------------
    # Archive I/O
    # ------------------------------------------------------------------

    def _load_archive(self, filepath):
        with zipfile.ZipFile(filepath, 'r') as zf:
            model_dict = json.loads(zf.read('model.json').decode())
            arrays_buf = io.BytesIO(zf.read('arrays.npz'))
        arrays = dict(np.load(arrays_buf, allow_pickle=False))
        return model_dict, arrays

    def _check_version(self, model_dict):
        file_ver = model_dict.get('brian_version', 'unknown')
        if file_ver != brian2.__version__:
            warnings.warn(
                f'Archive was created with Brian {file_ver}; '
                f'current Brian is {brian2.__version__}. '
                'This may cause compatibility issues.',
                UserWarning,
                stacklevel=3,
            )
