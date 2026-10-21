"""No-model fixtures; test observations come from actual loopback TLS sockets."""
import importlib.util
import pathlib
import tempfile
import threading
import unittest

_PATH = pathlib.Path(__file__).with_name("padding.py")
_SPEC = importlib.util.spec_from_file_location("padding_experiment", _PATH)
p = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(p)


class PaddingTests(unittest.TestCase):
    def test_application_identity_and_padding_corruption(self):
        for text in ("", "short", "工具与状态 " * 80):
            for padded in (False, True):
                frames = p.encode_message(text, padded)
                self.assertEqual(text, p.decode_message(b"".join(frames), padded))
                if padded:
                    self.assertEqual([1024] * 16, [len(f) for f in frames])
        encoded = bytearray(b"".join(p.encode_message("short", True)))
        encoded[-1] = 1
        with self.assertRaises(ValueError):
            p.decode_message(bytes(encoded), True)
        with self.assertRaises(ValueError):
            p.encode_message("x" * p.PAD_CAPACITY, True)

    def test_tls_parser_segmentation_invariance_and_truncation(self):
        stream = b"\x16\x03\x03\x00\x02hh\x17\x03\x03\x00\x03abc"
        parsed = p.parse_tls(stream, [{"offset": 0, "length": len(stream), "read_ns": 1}])
        self.assertEqual(3, parsed["application_payload_bytes"])
        self.assertEqual(1, parsed["application_record_count"])
        with self.assertRaises(ValueError):
            p.parse_tls(stream[:-1], [])

    def test_label_threshold_does_not_fit_constant(self):
        rows = [{"feature": 100, "label": label} for label in (0, 1) for _ in range(12)]
        self.assertEqual({"kind": "constant", "label": 0}, p.fit_threshold(rows))

    def test_topic_pair_split_validation(self):
        records = [{"id": str(label), "group_id": "one", "label": label,
                    "split": "train", "text": "a", "status": "ok"} for label in (0, 1)]
        p.validate_records(records, expected_groups=None)
        records[1]["split"] = "test"
        with self.assertRaises(ValueError):
            p.validate_records(records, expected_groups=None)

    def test_real_tls_padding_placement_integrity_and_thread_closure(self):
        initial_threads = {t.ident for t in threading.enumerate()}
        with tempfile.TemporaryDirectory() as temp:
            directory = pathlib.Path(temp)
            cert, key = p.certificate(directory / "cert")
            server, client = p.contexts(cert, key)
            outputs = {}
            for arm in p.ARMS:
                for label, text in ((0, "a" * 80), (1, "b" * 1100)):
                    report = p.replay(text, arm, directory / arm / str(label), server, client)
                    self.assertEqual("ok", report["status"], report["error"])
                    self.assertEqual(report["source_sha256"], report["terminal_sha256"])
                    self.assertTrue(report["all_owned_threads_joined"])
                    outputs[arm, label] = report
                    for site in ("upstream", "terminal"):
                        raw = (directory / arm / str(label) / "observer" / (site + "-s2c.bin")).read_bytes()
                        self.assertNotIn(text.encode(), raw)
            def feature(arm, label, site):
                return outputs[arm, label]["sites"][site]["s2c"]["application_payload_bytes"]
            for site in ("upstream", "terminal"):
                self.assertNotEqual(feature("NONE", 0, site), feature("NONE", 1, site))
                self.assertEqual(feature("END_TO_END_PAD", 0, site), feature("END_TO_END_PAD", 1, site))
            self.assertEqual(feature("UPSTREAM_PAD", 0, "upstream"), feature("UPSTREAM_PAD", 1, "upstream"))
            self.assertNotEqual(feature("UPSTREAM_PAD", 0, "terminal"), feature("UPSTREAM_PAD", 1, "terminal"))
            self.assertEqual(feature("NONE", 0, "terminal"), feature("UPSTREAM_PAD", 0, "terminal"))
        self.assertEqual(initial_threads, {t.ident for t in threading.enumerate()})


if __name__ == "__main__":
    unittest.main(verbosity=2)
