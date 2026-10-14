"""Integration regressions on the saved real ZTO receipt and parent interval."""
import copy
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import anchored_payment as a

HERE = Path(__file__).resolve().parent.relative_to(Path.cwd())


class AnchoredPaymentTests(unittest.TestCase):
    def setUp(self):
        self.inputs = [a.payment.load(HERE / name) for name in
                       ('example.transcript.json', 'example.policy.json',
                        'anchor-evidence.json', 'anchor-expectations.json')]

    def review(self, limit=11):
        return a.review(*self.inputs, limit)

    def test_historical_acceptance_and_no_mutation(self):
        before = copy.deepcopy(self.inputs)
        report = self.review()
        self.assertTrue(report['accepted'])
        self.assertEqual(report['parentWalk']['linksChecked'], 11)
        self.assertEqual(report['payment']['paymentPolicy']['token'], 'ZTO')
        self.assertEqual(before, self.inputs)

    def test_broken_middle_link(self):
        self.inputs[2]['headers'][5]['parentHash'] = self.inputs[2]['headers'][0]['hash']
        self.assertIn('parent_walk_not_connected', self.review()['alerts'])

    def test_connected_walk_cannot_replace_payment_policy(self):
        amount = str(int(self.inputs[1]['minimum_raw']) + 1)
        self.inputs[1]['minimum_raw'] = amount
        self.inputs[0]['policy']['minimum_raw'] = amount
        result = self.review()
        self.assertTrue(result['parentWalk']['accepted'])
        self.assertFalse(result['accepted'])
        self.assertIn('payment_policy_not_met', result['alerts'])

    def test_policy_must_be_independent(self):
        self.inputs[0]['policy']['minimum_raw'] = '1'
        with self.assertRaises(ValueError):
            self.review()

    def test_short_connected_interval(self):
        evidence, anchors = self.inputs[2:]
        evidence['headers'].pop()
        last = evidence['headers'][-1]
        anchors['upper'] = {'number': int(last['number'], 16), 'hash': last['hash']}
        evidence['anchors'] = copy.deepcopy(anchors)
        evidence['rereads'][1] = copy.deepcopy(last)
        result = self.review()
        self.assertTrue(result['parentWalk']['accepted'])
        self.assertIn('walk_shorter_than_confirmation_policy', result['alerts'])

    def test_other_connected_interval_is_not_this_inclusion(self):
        evidence, anchors = self.inputs[2:]
        evidence['headers'].pop(0)
        first = evidence['headers'][0]
        anchors['lower'] = {'number': int(first['number'], 16), 'hash': first['hash']}
        evidence['anchors'] = copy.deepcopy(anchors)
        evidence['rereads'][0] = copy.deepcopy(first)
        self.assertIn('lower_anchor_is_not_payment_inclusion', self.review()['alerts'])

    def test_budget_never_truncates(self):
        for limit in (0, 10, 65, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.review(limit)

    def test_independent_anchor_mismatch(self):
        self.inputs[3]['upper']['hash'] = self.inputs[3]['lower']['hash']
        with self.assertRaises(ValueError):
            self.review()

    def test_commitment_covers_walk_and_budget(self):
        original = self.review()['commitment']['digest']
        self.assertNotEqual(original, self.review(12)['commitment']['digest'])
        self.inputs[2]['source'] = 'https://eth.drpc.org'
        self.assertNotEqual(original, self.review()['commitment']['digest'])

    def test_transport_disabled(self):
        with self.assertRaises(ValueError):
            a.bridge.collect(self.inputs[3], 11)

    def test_upper_anchor_ahead_of_observed_head(self):
        checked = a.payment.check(*self.inputs[:2])
        checked['settlementAndPayment']['head'] = self.inputs[3]['lower'].copy()
        with patch.object(a.payment, 'check', return_value=checked):
            self.assertIn('upper_anchor_ahead_of_payment_observation', self.review()['alerts'])

    def test_shared_height_conflict(self):
        checked = a.payment.check(*self.inputs[:2])
        checked['settlementAndPayment']['finalizedHead'] = {
            'number': self.inputs[3]['upper']['number'],
            'hash': self.inputs[3]['lower']['hash']}
        with patch.object(a.payment, 'check', return_value=checked):
            self.assertIn('finalizedHead_conflicts_with_walk', self.review()['alerts'])

    def test_report_bound(self):
        with patch.object(a, 'MAX_OUTPUT', 100), self.assertRaises(ValueError):
            self.review()

    def test_cli_and_input_error(self):
        args = [str(HERE / name) for name in ('example.transcript.json',
                'example.policy.json', 'anchor-evidence.json', 'anchor-expectations.json')]
        for suffix, expected in ((['--max-links', '11'], 0), (['--max-links', '10'], 2)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = a.main(args + suffix)
            self.assertEqual(code, expected)
            self.assertEqual(json.loads(out.getvalue())['accepted'], expected == 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
