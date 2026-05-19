"""
Tests for NumPy 1.x / 2.x compatible pickle I/O of export data.
"""
import io
import pickle
import unittest

import numpy as np
from brian2 import Hz, ms

from brian2tools.serialization import (
    NumpyCompatUnpickler,
    decode_export_data,
    dumps_runs,
    encode_export_data,
    load_runs,
    loads_runs,
)


class TestSerialization(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        original = {
            "record": np.array([0, 2, 4]),
            "weights": np.array([1.0, 2.5]),
            "scalar": np.int64(3),
            "nested": [{"idx": np.array([1])}],
        }
        restored = decode_export_data(encode_export_data(original))
        np.testing.assert_array_equal(restored["record"], original["record"])
        np.testing.assert_array_equal(restored["weights"], original["weights"])
        self.assertEqual(restored["scalar"], original["scalar"])
        np.testing.assert_array_equal(
            restored["nested"][0]["idx"], original["nested"][0]["idx"]
        )

    def test_portable_pickle_roundtrip(self):
        runs = [
            {
                "duration": 100 * ms,
                "components": {
                    "spikemonitor": [
                        {"record": np.array([0, 1]), "rates": np.arange(3) * Hz}
                    ]
                },
            }
        ]
        blob = dumps_runs(runs, portable=True)
        # Portable blobs must not reference NumPy internal pickle modules
        self.assertNotIn(b"numpy._core", blob)
        self.assertNotIn(b"numpy.core", blob)
        restored = loads_runs(blob, portable=True)
        self.assertEqual(restored[0]["duration"], runs[0]["duration"])
        np.testing.assert_array_equal(
            restored[0]["components"]["spikemonitor"][0]["record"],
            runs[0]["components"]["spikemonitor"][0]["record"],
        )
        np.testing.assert_array_equal(
            np.asarray(restored[0]["components"]["spikemonitor"][0]["rates"]),
            np.asarray(runs[0]["components"]["spikemonitor"][0]["rates"]),
        )

    def test_compat_unpickler_numpy2_array(self):
        arr = np.array([1, 2, 3])
        raw = pickle.dumps(arr)
        loaded = NumpyCompatUnpickler(io.BytesIO(raw)).load()
        np.testing.assert_array_equal(loaded, arr)

    def test_legacy_compat_load(self):
        """Bare ndarray pickles load via NumpyCompatUnpickler."""
        runs = [{"record": np.array([7, 8])}]
        buf = io.BytesIO()
        pickle.dump(runs, buf, protocol=pickle.HIGHEST_PROTOCOL)
        buf.seek(0)
        restored = load_runs(buf, portable=False)
        np.testing.assert_array_equal(restored[0]["record"], runs[0]["record"])


if __name__ == "__main__":
    unittest.main()
