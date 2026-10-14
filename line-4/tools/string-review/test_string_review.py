import contextlib
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import string_review as sr
from typed_digest import TypedDataError, digest, keccak256, loads_bounded


def data(text='ZTO'):
    return {'types': {'EIP712Domain': [{'name': 'name', 'type': 'string'}],
                      'Note': [{'name': 'memo', 'type': 'string'}]},
            'primaryType': 'Note', 'domain': {'name': 'ZTO'}, 'message': {'memo': text}}


class ReviewTests(unittest.TestCase):
    def memo(self, text):
        return sr.review(data(text))['strings'][1]

    def test_historical_zto_digest(self):
        example = loads_bounded(Path(__file__).with_name('zto-payment.json').read_bytes())
        result = sr.review(example, '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774')
        self.assertTrue(result['matchesExpected'])
        self.assertFalse(result['needsReview'])

    def test_ascii_and_empty(self):
        for text in ('', 'ZTO payment', 'ASCII 123'):
            item = self.memo(text)
            self.assertFalse(item['needsReview'])
            self.assertEqual(item['word'], '0x' + keccak256(text.encode()).hex())

    def test_bidi_override_escaped_on_output(self):
        report = sr.review(data('ZTO\u202e123'))
        item = report['strings'][1]['cues'][0]
        self.assertEqual((item['codePoint'], item['utf8OffsetBytes']), ('U+202E', 3))
        self.assertEqual(item['bidirectionalClass'], 'RLO')
        self.assertIn('control_format_or_unassigned', item['reasons'])
        self.assertNotIn('\u202e', sr.render(report))
        self.assertIn('\\u202e', sr.render(report))

    def test_zero_width_space(self):
        self.assertTrue(self.memo('Z\u200bTO')['needsReview'])
        self.assertNotEqual(sr.review(data('ZTO'))['digest'], sr.review(data('Z\u200bTO'))['digest'])

    def test_offsets_are_utf8_not_utf16(self):
        item = self.memo('\U0001f438\u200b')
        self.assertEqual(item['scalarCount'], 2)
        self.assertEqual(item['utf8Bytes'], 7)
        self.assertEqual(item['cues'][1]['scalarIndex'], 1)
        self.assertEqual(item['cues'][1]['utf8OffsetBytes'], 4)

    def test_nfc_not_substituted(self):
        original = data('e\u0301')
        before = copy.deepcopy(original)
        result = sr.review(original)
        item = result['strings'][1]
        self.assertEqual(original, before)
        self.assertEqual(result['digest'], digest(original)['digest'])
        self.assertNotEqual(result['digest'], digest(data('\u00e9'))['digest'])
        self.assertEqual(item['normalizationAlternatives'][0]['value'], '\u00e9')
        self.assertEqual(item['utf8Hex'], '65cc81')
        self.assertIn('combining_or_enclosing_mark', item['cues'][0]['reasons'])

    def test_nfkc_fullwidth(self):
        item = self.memo('\uff3a\uff34\uff2f')
        self.assertEqual([x['form'] for x in item['normalizationAlternatives']], ['NFKC'])
        self.assertEqual(item['normalizationAlternatives'][0]['value'], 'ZTO')

    def test_legitimate_non_ascii_is_review_not_invalid(self):
        self.assertTrue(self.memo('\u65e5\u672c')['needsReview'])

    def test_whitespace_and_controls(self):
        for text, reason in [(' ZTO', 'edge_whitespace'), ('ZTO ', 'edge_whitespace'),
                             ('Z\tTO', 'control_format_or_unassigned'),
                             ('Z\nTO', 'control_format_or_unassigned'),
                             ('Z\x00TO', 'control_format_or_unassigned'),
                             ('Z\x7fTO', 'control_format_or_unassigned'),
                             ('Z\u00a0TO', 'non_space_separator')]:
            with self.subTest(text=text):
                cues = self.memo(text)['cues']
                self.assertTrue(any(reason in cue['reasons'] for cue in cues))

    def test_variation_selector(self):
        item = self.memo('\u2764\ufe0f')
        self.assertIn('combining_or_enclosing_mark', item['cues'][1]['reasons'])

    def test_domain_and_nested_arrays(self):
        request = data()
        request['domain']['name'] = 'Z\u200bTO'
        request['types']['Note'] = [{'name': 'nested', 'type': 'Leaf[][1]'}]
        request['types']['Leaf'] = [{'name': 'text', 'type': 'string'}]
        request['message'] = {'nested': [[{'text': '\u202e'}]]}
        result = sr.review(request)
        self.assertEqual([s['path'] for s in result['strings']],
                         ['/domain/name', '/message/nested/0/0/text'])
        self.assertTrue(all(s['needsReview'] for s in result['strings']))

    def test_bytes_and_unreachable_schema_not_strings(self):
        request = data()
        request['types']['Note'] = [{'name': 'raw', 'type': 'bytes'}]
        request['types']['Unused'] = [{'name': 'hidden', 'type': 'string'}]
        request['message'] = {'raw': '0x202e'}
        self.assertEqual(sr.review(request)['stringCount'], 1)

    def test_no_strings(self):
        request = data()
        request['types']['EIP712Domain'] = []
        request['domain'] = {}
        request['types']['Note'] = []
        request['message'] = {}
        self.assertEqual(sr.review(request)['strings'], [])

    def test_validation_precedes_walk(self):
        request = data()
        request['message']['extra'] = 'bad'
        with self.assertRaises(TypedDataError):
            sr.review(request)
        with self.assertRaises(TypedDataError):
            sr.review(data('\ud800'))
        with self.assertRaises(TypedDataError):
            sr.review(data(), '0x1234')

    def test_digest_mismatch(self):
        result = sr.review(data('ZTO'), digest(data('IMD'))['digest'])
        self.assertFalse(result['matchesExpected'])

    def test_output_bound_fails_closed(self):
        with self.assertRaisesRegex(TypedDataError, 'output limit'):
            sr.review(data('\u200b' * 1000))

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(TypedDataError):
            loads_bounded(b'{"message":{},"message":{}}')

    def test_cli_exit_codes_and_no_partial_output(self):
        for request, expected_code in [(data(), 0), (data('\u202e'), 1), (data('\u200b' * 1000), 2)]:
            output, error = io.StringIO(), io.StringIO()
            with patch.object(sr, 'load_workspace_json', return_value=request), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                self.assertEqual(sr.main(['input.json']), expected_code)
            if expected_code == 2:
                self.assertEqual(output.getvalue(), '')
                self.assertIn('output limit', error.getvalue())
            else:
                json.loads(output.getvalue())

    def test_cli_digest_mismatch(self):
        with patch.object(sr, 'load_workspace_json', return_value=data()), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sr.main(['input.json', '--expect', digest(data('IMD'))['digest']]), 1)

    def test_workspace_boundary_without_open(self):
        with self.assertRaises(TypedDataError):
            sr.load_workspace_json('../outside.json')
        with self.assertRaises(TypedDataError):
            sr.load_workspace_json('.hidden/input.json')


if __name__ == '__main__':
    unittest.main()
