"""
Portable pickle I/O for baseexport ``device.runs`` data.

NumPy 1.x pickles reference ``numpy.core.*``; NumPy 2.x uses ``numpy._core.*``.
Raw pickles of ndarray objects therefore fail across major versions.

Two strategies are supported:

* **portable=True** (default): encode ndarrays as plain metadata before pickling.
  This works across NumPy 1.x and 2.x without relying on module remapping.
* **portable=False**: pickle objects directly and use :class:`NumpyCompatUnpickler`
  to remap ``numpy.core`` <-> ``numpy._core`` when loading legacy files.
"""
from __future__ import annotations

import io
import pickle
from typing import Any, BinaryIO

import numpy as np

from brian2.units.fundamentalunits import (
    Dimension,
    Quantity,
    Unit,
    get_or_create_dimension,
    quantity_with_dimensions,
)

_ARRAY_TAG = "__brian2tools_numpy_array__"
_SCALAR_TAG = "__brian2tools_numpy_scalar__"
_QUANTITY_TAG = "__brian2tools_quantity__"
_DIMENSION_TAG = "__brian2tools_dimension__"

_NUMPY_CORE_PREFIXES = ("numpy.core.", "numpy._core.")


def _numpy_module_alt(module: str) -> str | None:
    if module.startswith("numpy._core."):
        return "numpy.core." + module[len("numpy._core.") :]
    if module.startswith("numpy.core."):
        return "numpy._core." + module[len("numpy.core.") :]
    return None


class NumpyCompatUnpickler(pickle.Unpickler):
    """Unpickler that remaps NumPy 1.x / 2.x internal module paths."""

    def find_class(self, module: str, name: str):
        alt = _numpy_module_alt(module)
        if alt is not None:
            try:
                return super().find_class(alt, name)
            except (AttributeError, ModuleNotFoundError, ImportError):
                pass
        return super().find_class(module, name)


def _encode_numpy(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return {
            _ARRAY_TAG: True,
            "data": obj.tolist(),
            "dtype": np.dtype(obj.dtype).str,
        }
    if isinstance(obj, np.generic):
        return {
            _SCALAR_TAG: True,
            "data": obj.item(),
            "dtype": np.dtype(obj.dtype).str,
        }
    return obj


def _dimension_dims(dim: Dimension | Unit) -> tuple:
    if isinstance(dim, Unit):
        return dim.dim._dims
    return dim._dims


def _encode_dimension(dim: Dimension | Unit) -> dict:
    return {_DIMENSION_TAG: True, "dims": _dimension_dims(dim)}


def _encode_quantity(q: Quantity) -> dict:
    return {
        _QUANTITY_TAG: True,
        "value": encode_export_data(np.asarray(q)),
        "dim": _encode_dimension(q.dim),
    }


def encode_export_data(obj: Any) -> Any:
    """
    Recursively replace NumPy and Brian unit types with portable representations.

    Bare ``ndarray`` / NumPy scalar objects and ``Quantity`` / ``Dimension``
    are encoded so pickles do not reference ``numpy.core`` or ``numpy._core``.
    """
    if isinstance(obj, Quantity):
        return _encode_quantity(obj)
    if isinstance(obj, Dimension):
        return _encode_dimension(obj)
    encoded = _encode_numpy(obj)
    if encoded is not obj:
        return encoded
    if isinstance(obj, dict):
        return {key: encode_export_data(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [encode_export_data(value) for value in obj]
    if isinstance(obj, tuple):
        return tuple(encode_export_data(value) for value in obj)
    return obj


def _decode_numpy(obj: Any) -> Any:
    if isinstance(obj, dict):
        if obj.get(_ARRAY_TAG):
            return np.array(obj["data"], dtype=np.dtype(obj["dtype"]))
        if obj.get(_SCALAR_TAG):
            return np.dtype(obj["dtype"]).type(obj["data"])
    return obj


def _decode_dimension(obj: dict) -> Dimension:
    return get_or_create_dimension(tuple(obj["dims"]))


def _decode_quantity(obj: dict) -> Quantity:
    value = decode_export_data(obj["value"])
    dim = _decode_dimension(obj["dim"])
    return quantity_with_dimensions(value, dim)


def decode_export_data(obj: Any) -> Any:
    """Restore objects encoded by :func:`encode_export_data`."""
    if isinstance(obj, dict):
        if obj.get(_QUANTITY_TAG):
            return _decode_quantity(obj)
        if obj.get(_DIMENSION_TAG):
            return _decode_dimension(obj)
    decoded = _decode_numpy(obj)
    if decoded is not obj:
        return decoded
    if isinstance(obj, dict):
        return {key: decode_export_data(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [decode_export_data(value) for value in obj]
    if isinstance(obj, tuple):
        return tuple(decode_export_data(value) for value in obj)
    return obj


def _needs_portable_decode(obj: Any) -> bool:
    if isinstance(obj, dict) and (
        _ARRAY_TAG in obj
        or _SCALAR_TAG in obj
        or _QUANTITY_TAG in obj
        or _DIMENSION_TAG in obj
    ):
        return True
    if isinstance(obj, dict):
        return any(_needs_portable_decode(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_needs_portable_decode(v) for v in obj)
    return False


def dump_runs(
    runs: Any,
    file: BinaryIO,
    *,
    portable: bool = True,
    protocol: int = pickle.HIGHEST_PROTOCOL,
) -> None:
    """
    Pickle export data from :attr:`~brian2tools.baseexport.device.BaseExporter.runs`.

    Parameters
    ----------
    runs
        The ``device.runs`` list (or compatible structure).
    file
        Writable binary file object.
    portable
        If ``True`` (default), encode NumPy arrays before pickling so the file
        loads on both NumPy 1.x and 2.x. If ``False``, rely on
        :class:`NumpyCompatUnpickler` when loading.
    protocol
        Pickle protocol passed to :func:`pickle.dump`.
    """
    payload = encode_export_data(runs) if portable else runs
    pickle.dump(payload, file, protocol=protocol)


def load_runs(
    file: BinaryIO,
    *,
    portable: bool = True,
) -> Any:
    """
    Load data written by :func:`dump_runs`.

    Parameters
    ----------
    file
        Readable binary file object.
    portable
        If ``True`` (default), decode portable NumPy representations after
        loading. Legacy files pickled without encoding are still loaded when
        they contain encoded markers or bare NumPy objects (via
        :class:`NumpyCompatUnpickler`).
    """
    data = NumpyCompatUnpickler(file).load()
    if portable or _needs_portable_decode(data):
        return decode_export_data(data)
    return data


def dumps_runs(runs: Any, **kwargs: Any) -> bytes:
    """Like :func:`dump_runs` but return ``bytes``."""
    buf = io.BytesIO()
    dump_runs(runs, buf, **kwargs)
    return buf.getvalue()


def loads_runs(data: bytes, **kwargs: Any) -> Any:
    """Like :func:`load_runs` but accept ``bytes``."""
    return load_runs(io.BytesIO(data), **kwargs)
