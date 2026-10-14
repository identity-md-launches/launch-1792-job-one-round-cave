#!/usr/bin/env python3
"""Bounded provider-observed parent links between explicit Ethereum anchors."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location('bridge_witness', Path(__file__).resolve().parent.parent / 'payment-witness' / 'witness.py')
w = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(w)
s = w.settlement
SOURCES = (s.RPC_URL, 'https://eth.drpc.org')
LIMIT = ('Provider-observed parent hashes, not cryptographically recomputed headers, consensus, '
         'receipt inclusion or a settlement decision. Anchors must be retained independently. '
         'Later reorgs remain possible; no claim is made outside this bounded interval.')


def anchor(value):
    if not isinstance(value, dict) or set(value) != {'number', 'hash'}:
        raise w.Error('anchor requires number and hash')
    if type(value['number']) is not int or not 0 <= value['number'] < 2**64:
        raise w.Error('invalid anchor height')
    return {'number': value['number'], 'hash': s.hash32(value['hash'])}


def validate(anchors, max_links):
    if type(max_links) is not int or not 1 <= max_links <= 64:
        raise w.Error('max links must be 1..64')
    if not isinstance(anchors, dict) or set(anchors) != {'lower', 'upper'}:
        raise w.Error('exactly two explicit anchors required')
    result = {key: anchor(anchors[key]) for key in ('lower', 'upper')}
    distance = result['upper']['number'] - result['lower']['number']
    if not 0 <= distance <= max_links:
        raise w.Error('reversed anchors or interval exceeds caller budget')
    if distance == 0 and result['lower'] != result['upper']:
        raise w.Error('same-height anchors conflict')
    return result


def header(raw, number):
    if not isinstance(raw, dict) or s.quantity(raw.get('number')) != number:
        raise w.Error('missing or wrong-height header')
    return {'number': hex(number), 'hash': s.hash32(raw.get('hash')),
            'parentHash': s.hash32(raw.get('parentHash'))}


def replay(sample, expected_anchors, max_links=64):
    expected = validate(expected_anchors, max_links)
    if (not isinstance(sample, dict) or set(sample) !=
            {'version', 'source', 'chainId', 'anchors', 'headers', 'rereads'}
            or type(sample['version']) is not int or sample['version'] != 1
            or sample['source'] not in SOURCES or sample['chainId'] != '0x1'
            or validate(sample['anchors'], max_links) != expected):
        raise w.Error('invalid bridge envelope or independently retained anchor mismatch')
    low, high = expected['lower']['number'], expected['upper']['number']
    if not isinstance(sample['headers'], list) or len(sample['headers']) != high-low+1:
        raise w.Error('incomplete or oversized bridge')
    headers = []
    for number, raw in zip(range(low, high+1), sample['headers']):
        if not isinstance(raw, dict) or set(raw) != {'number', 'hash', 'parentHash'}:
            raise w.Error('invalid compact header')
        headers.append(header(raw, number))
    rereads = sample['rereads']
    if not isinstance(rereads, list) or len(rereads) != 2:
        raise w.Error('both endpoint rereads required')
    repeated = []
    for number, raw in zip((low, high), rereads):
        if not isinstance(raw, dict) or set(raw) != {'number', 'hash', 'parentHash'}:
            raise w.Error('invalid endpoint reread')
        repeated.append(header(raw, number))
    alerts = []
    if headers[0]['hash'] != expected['lower']['hash']:
        alerts.append('lower_anchor_changed')
    if headers[-1]['hash'] != expected['upper']['hash']:
        alerts.append('upper_anchor_changed')
    if repeated != [headers[0], headers[-1]]:
        alerts.append('endpoint_changed_during_collection')
    if len({item['hash'] for item in headers}) != len(headers):
        alerts.append('block_hash_reused')
    broken = [low+i for i in range(1, len(headers))
              if headers[i]['parentHash'] != headers[i-1]['hash']]
    if broken:
        alerts.append('parent_link_broken')
    return {'accepted': not alerts,
            'state': 'observed_ancestry_connected' if not alerts else 'review_required',
            'anchors': expected, 'linksChecked': high-low, 'brokenAtHeights': broken,
            'alerts': alerts, 'source': sample['source'],
            'evidenceMode': 'offline replay of provider-observed parent links', 'evidenceLimit': LIMIT}


def collect(expected_anchors, max_links=64, source=SOURCES[0], rpc_factory=s.RPC):
    anchors = validate(expected_anchors, max_links)
    if source not in SOURCES:
        raise w.Error('documented public source required')
    rpc = rpc_factory(source)  # No transport exists until all inputs pass.
    if s.quantity(rpc.call('eth_chainId', [])) != 1:
        raise w.Error('Ethereum mainnet required')
    low, high = anchors['lower']['number'], anchors['upper']['number']
    # Descend through every numeric canonical header; check every parent link on replay.
    headers = [header(rpc.call('eth_getBlockByNumber', [hex(n), False]), n)
               for n in range(high, low-1, -1)]
    sample = {'version': 1, 'source': source, 'chainId': '0x1', 'anchors': anchors,
              'headers': list(reversed(headers)),
              'rereads': [header(rpc.call('eth_getBlockByNumber', [hex(n), False]), n)
                          for n in (low, high)]}
    result = replay(sample, anchors, max_links)
    result.update(sample=sample, evidenceMode='live sequential public reads; endpoints reread')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--demo', action='store_true')
    mode.add_argument('--replay')
    mode.add_argument('--live', action='store_true')
    parser.add_argument('--anchors', help='workspace-relative independently retained anchor JSON')
    parser.add_argument('--max-links', type=int, default=64)
    parser.add_argument('--rpc', choices=SOURCES)
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if args.anchors is not None or args.rpc is not None or args.max_links != 64:
                raise w.Error('demo refuses overrides')
            folder = Path(__file__).resolve().parent.relative_to(Path.cwd())
            expected = w.load_workspace_json(folder / 'demo-anchors.json')
            result = replay(w.load_workspace_json(folder / 'live-evidence.json'), expected)
            result['demoNote'] = ('Real ZTO inclusion and its eleventh successor; illustrative saved '
                                  'anchors, not independent approval or present settlement.')
        else:
            if args.anchors is None or (args.rpc is not None and not args.live):
                raise w.Error('anchors required; RPC applies only to live collection')
            expected = validate(w.load_workspace_json(args.anchors), args.max_links)
            result = (collect(expected, args.max_links, args.rpc or SOURCES[0]) if args.live else
                      replay(w.load_workspace_json(args.replay), expected, args.max_links))
        encoded = json.dumps(result, indent=2, allow_nan=False)
        if len(encoded.encode()) > 100000:
            raise w.Error('output too large')
        print(encoded)
        return 0 if result['accepted'] else 1
    except (w.Error, ValueError, TypeError, KeyError, OSError, RecursionError):
        print(json.dumps({'accepted': False, 'state': 'input_error',
                          'reason': 'Invalid anchors, evidence, budget or unavailable public read'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
