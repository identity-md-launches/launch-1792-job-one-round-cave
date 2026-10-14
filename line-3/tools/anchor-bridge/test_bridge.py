import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).with_name('bridge.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
FOLDER = Path(__file__).parent


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.sample = json.loads((FOLDER / 'live-evidence.json').read_text())
        self.anchors = json.loads((FOLDER / 'demo-anchors.json').read_text())

    def check(self):
        return b.replay(self.sample, self.anchors, 11)

    def test_real_zto_interval(self):
        result = self.check()
        self.assertTrue(result['accepted'])
        self.assertEqual(result['linksChecked'], 11)

    def test_exact_budget(self):
        with self.assertRaises(b.w.Error):
            b.replay(self.sample, self.anchors, 10)

    def test_invalid_budgets_before_transport(self):
        for budget in (True, 0, 65, '11', 11.0):
            with self.subTest(budget=budget), self.assertRaises(b.w.Error):
                b.collect(self.anchors, budget, rpc_factory=lambda url: self.fail('transport constructed'))

    def test_reverse_anchors(self):
        self.anchors = dict(lower=self.anchors['upper'], upper=self.anchors['lower'])
        with self.assertRaises(b.w.Error):
            self.check()

    def test_boolean_height(self):
        self.anchors['lower']['number'] = True
        with self.assertRaises(b.w.Error):
            self.check()

    def test_expected_hash_mismatch(self):
        self.anchors['upper']['hash'] = self.anchors['lower']['hash']
        with self.assertRaises(b.w.Error):
            self.check()

    def test_anchor_lost_on_chain(self):
        self.sample['headers'][0]['hash'] = self.sample['headers'][1]['hash']
        result = self.check()
        self.assertFalse(result['accepted'])
        self.assertIn('lower_anchor_changed', result['alerts'])

    def test_broken_middle_link(self):
        self.sample['headers'][6]['parentHash'] = self.sample['headers'][2]['hash']
        result = self.check()
        self.assertEqual(result['brokenAtHeights'], [self.anchors['lower']['number']+6])
        self.assertFalse(result['accepted'])

    def test_wrong_number(self):
        self.sample['headers'][4]['number'] = self.sample['headers'][3]['number']
        with self.assertRaises(b.w.Error):
            self.check()

    def test_reordered(self):
        self.sample['headers'].reverse()
        with self.assertRaises(b.w.Error):
            self.check()

    def test_missing_header(self):
        self.sample['headers'].pop(4)
        with self.assertRaises(b.w.Error):
            self.check()

    def test_extra_header(self):
        self.sample['headers'].append(self.sample['headers'][-1])
        with self.assertRaises(b.w.Error):
            self.check()

    def test_extra_fields(self):
        for target in (self.sample, self.sample['headers'][3], self.sample['rereads'][0]):
            target['accepted'] = True
            with self.assertRaises(b.w.Error):
                self.check()
            del target['accepted']

    def test_wrong_chain(self):
        self.sample['chainId'] = '0x2'
        with self.assertRaises(b.w.Error):
            self.check()

    def test_wrong_source(self):
        self.sample['source'] = 'https://example.org'
        with self.assertRaises(b.w.Error):
            self.check()

    def test_boolean_version(self):
        self.sample['version'] = True
        with self.assertRaises(b.w.Error):
            self.check()

    def test_missing_reread(self):
        self.sample['rereads'].pop()
        with self.assertRaises(b.w.Error):
            self.check()

    def test_changed_endpoint_parent(self):
        self.sample['rereads'][1]['parentHash'] = self.sample['headers'][0]['hash']
        self.assertIn('endpoint_changed_during_collection', self.check()['alerts'])

    def test_invalid_parent_hash(self):
        self.sample['headers'][3]['parentHash'] = None
        with self.assertRaises(b.w.Error):
            self.check()

    def test_same_height(self):
        one = self.sample['headers'][0]
        anchors = dict(lower=self.anchors['lower'], upper=self.anchors['lower'])
        sample = dict(self.sample, anchors=anchors, headers=[one], rereads=[one, one])
        result = b.replay(sample, anchors, 1)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['linksChecked'], 0)

    def test_same_height_conflict(self):
        self.anchors['upper']['number'] = self.anchors['lower']['number']
        with self.assertRaises(b.w.Error):
            self.check()

    def test_collect_replay_request_order(self):
        reads = [('eth_chainId', [], '0x1')]
        for h in reversed(self.sample['headers']):
            reads.append(('eth_getBlockByNumber', [h['number'], False], h))
        for h in self.sample['rereads']:
            reads.append(('eth_getBlockByNumber', [h['number'], False], h))
        class RPC:
            def call(inner, method, params):
                m, p, result = reads.pop(0)
                self.assertEqual((method, params), (m, p))
                return result
        result = b.collect(self.anchors, 11, rpc_factory=lambda url: RPC())
        self.assertTrue(result['accepted'])
        self.assertEqual(result['sample'], self.sample)
        self.assertEqual(reads, [])

    def test_null_provider_header(self):
        class RPC:
            def call(inner, method, params):
                return '0x1' if method == 'eth_chainId' else None
        with self.assertRaises(b.w.Error):
            b.collect(self.anchors, 11, rpc_factory=lambda url: RPC())

    def test_unsupported_source_before_transport(self):
        with self.assertRaises(b.w.Error):
            b.collect(self.anchors, 11, 'https://example.org',
                      rpc_factory=lambda url: self.fail('transport constructed'))

    def test_demo_cli(self):
        import contextlib
        import io
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = b.main(['--demo'])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())['accepted'])


if __name__ == '__main__':
    unittest.main()
