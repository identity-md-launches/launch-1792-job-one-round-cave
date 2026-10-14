"""Offline guard regressions; fixtures exist only under test/scratch/."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('source_guard', Path(__file__).with_name('review.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader, cls.source, cls.engine, cls.rules = guard.dependencies()
        Path('test/scratch').mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='test/scratch')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).absolute().relative_to(Path.cwd())
        self.c, self.d, self.r = [str(self.root / n) for n in ('contract.json', 'document.json', 'report.json')]
        Path(self.c).write_bytes(b'{"type":"object","properties":{"x":{"type":"integer"}},"required":["x"],"additionalProperties":false}')
        Path(self.d).write_bytes('{\r\n "x": "é", "extra": null\r\n}'.encode())
        self.saved = self.regenerate()
        self.save()

    def regenerate(self):
        return self.source.locate(self.engine, self.rules,
            self.source.Source(Path(self.c).read_bytes(), self.c),
            self.source.Source(Path(self.d).read_bytes(), self.d))

    def save(self):
        Path(self.r).write_text(json.dumps(self.saved), encoding='utf-8')

    def review(self, pin=None):
        return guard.review(self.reader, self.source, self.engine, self.rules,
                            self.r, self.c, self.d, pin)

    def status(self, wanted):
        result, code = self.review()
        self.assertEqual(result['status'], wanted)
        self.assertEqual(code, 1)
        self.assertFalse(result['matches'])

    def test_invalid_document_report_reproduced(self):
        result, code = self.review()
        self.assertEqual(code, 0)
        self.assertFalse(result['document_valid'])
        self.assertEqual(result['error_count'], 2)

    def test_valid_document(self):
        Path(self.d).write_text('{"x":1}')
        self.saved = self.regenerate(); self.save()
        result, code = self.review()
        self.assertEqual(code, 0)
        self.assertTrue(result['document_valid'])

    def test_document_whitespace_changed(self):
        with Path(self.d).open('ab') as file: file.write(b' ')
        self.status('source_identity_mismatch')

    def test_contract_whitespace_changed(self):
        with Path(self.c).open('ab') as file: file.write(b'\n')
        self.status('source_identity_mismatch')

    def test_modified_range(self):
        self.saved['errors'][0]['document_source']['value']['start']['byte_offset'] += 1
        self.save(); self.status('diagnostic_mismatch')

    def test_boolean_cannot_replace_integer(self):
        self.saved['errors'][0]['document_source']['value']['start']['line'] = True
        self.save(); self.status('diagnostic_mismatch')

    def test_removed_diagnostic(self):
        self.saved['errors'].pop(); self.save()
        self.status('diagnostic_mismatch')

    def test_changed_preview(self):
        self.saved['errors'][0]['observed']['preview'] = 'other'
        self.save(); self.status('diagnostic_mismatch')

    def test_report_pin(self):
        pin = hashlib.sha256(Path(self.r).read_bytes()).hexdigest()
        self.assertEqual(self.review(pin)[1], 0)
        Path(self.r).write_bytes(Path(self.r).read_bytes() + b' ')
        self.assertEqual(self.review(pin)[0]['status'], 'report_pin_mismatch')

    def test_bad_pin_before_document_access(self):
        Path(self.d).unlink()
        result, code = self.review('0'*64)
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'report_pin_mismatch')

    def test_embedded_path_is_never_opened(self):
        # A recording reader makes the boundary explicit without any external read.
        self.saved['sources']['document']['file'] = 'forbidden/path'
        self.save()
        names = []
        class Reader:
            def read_bytes(inner, name):
                names.append(name)
                return self.reader.read_bytes(name)
        result, code = guard.review(Reader(), self.source, self.engine, self.rules,
                                   self.r, self.c, self.d)
        self.assertEqual(code, 1)
        self.assertEqual(names, [self.r, self.c, self.d])

    def test_missing_field_anchor(self):
        Path(self.d).write_text('{}')
        self.saved = self.regenerate(); self.save()
        self.assertFalse(self.saved['errors'][0]['document_source']['present'])
        self.assertEqual(self.review()[1], 0)

    def test_symlink_refused(self):
        link = self.root / 'linked.json'; link.symlink_to('document.json')
        with self.assertRaises(OSError):
            guard.review(self.reader, self.source, self.engine, self.rules,
                         self.r, self.c, str(link))

    def test_duplicate_report_key_refused(self):
        Path(self.r).write_text('{"sources":{},"sources":{}}')
        with self.assertRaises(ValueError): self.review()

    def test_malformed_source_refused(self):
        Path(self.d).write_text('{')
        with self.assertRaises(ValueError): self.review()

    def test_extra_report_field_rejected(self):
        self.saved['approved'] = True; self.save()
        self.status('diagnostic_mismatch')

    def test_diagnostic_order_rejected(self):
        self.saved['errors'].reverse(); self.save()
        self.status('diagnostic_mismatch')

    def test_invalid_pin_syntax(self):
        with self.assertRaises(ValueError): self.review('invalid')


if __name__ == '__main__':
    unittest.main()
