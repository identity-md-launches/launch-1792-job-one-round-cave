#!/usr/bin/env python3
"""Require both a payment policy and a bounded, explicitly anchored parent walk."""
import argparse
import json
import check as payment

bridge = payment.module('payment_anchor_bridge', 'vendor/anchor-bridge/bridge.py')
MAX_OUTPUT = 100000


def render(result):
    raw = json.dumps(result, ensure_ascii=True, indent=2) + '\n'
    if len(raw.encode('ascii')) > MAX_OUTPUT:
        raise ValueError('combined report exceeds 100000 bytes')
    return raw


def review(transcript, policy, evidence, anchors, max_links):
    expected = bridge.validate(anchors, max_links)
    checked = payment.check(transcript, policy)
    walk = bridge.replay(evidence, expected, max_links)
    facts = checked['settlementAndPayment']
    alerts = []
    if not checked['accepted']:
        alerts.append('payment_policy_not_met')
    if not walk['accepted']:
        alerts.append('parent_walk_not_connected')
    if expected['lower'] != facts.get('inclusion'):
        alerts.append('lower_anchor_is_not_payment_inclusion')
    if expected['upper']['number'] > facts['head']['number']:
        alerts.append('upper_anchor_ahead_of_payment_observation')
    if expected['upper']['number'] - expected['lower']['number'] + 1 < policy['confirmations']:
        alerts.append('walk_shorter_than_confirmation_policy')
    # Any equal-height facts in the two independently replayed inputs must agree.
    known = {int(h['number'], 16): h['hash'] for h in evidence['headers']}
    for key in ('inclusion', 'head', 'finalizedHead'):
        value = facts.get(key)
        if value and value['number'] in known and known[value['number']] != value['hash']:
            alerts.append(key + '_conflicts_with_walk')
    # Bind all observations, independent anchors and caller budget, not merely a
    # passing flag. This uses the existing Line 4 EIP-712 content encoder.
    bundle = {'payment': transcript, 'parentWalk': evidence,
              'expectedAnchors': expected, 'maxLinks': max_links}
    data, digest = payment.commitment(bundle, policy)
    result = {'accepted': not alerts,
              'state': 'payment_and_bounded_ancestry_match' if not alerts else 'review_required',
              'alerts': alerts, 'payment': facts, 'parentWalk': walk,
              'typedData': data, 'commitment': digest,
              'evidenceLimit': 'Historical provider assertions, not header/receipt proofs or current settlement. '
                               'The walk need not reach the sampled head or finalized head. '
                               'Caller anchors and policy must be chosen independently. '
                               'Digest equality is not authorization.'}
    render(result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transcript')
    parser.add_argument('policy')
    parser.add_argument('evidence')
    parser.add_argument('anchors')
    parser.add_argument('--max-links', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        # Validate independent policy and budget before submitted evidence.
        policy = payment.policy(payment.load(args.policy))
        anchors = bridge.validate(payment.load(args.anchors), args.max_links)
        result = review(payment.load(args.transcript), policy,
                        payment.load(args.evidence), anchors, args.max_links)
        print(render(result), end='')
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, TypeError, KeyError, RecursionError):
        print('{"accepted":false,"state":"input_error"}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
