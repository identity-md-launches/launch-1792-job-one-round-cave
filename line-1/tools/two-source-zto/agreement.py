#!/usr/bin/env python3
"""Capture or replay two providers' ZTO reads at one finalized block hash."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import sys
import urllib.error
import urllib.request


P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                       'hash-pinned-zto' / 'pinned.py'))
B = P['B']
SAFE = P['SAFE']
SOURCES = ('https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org')
SCHEMA = 'line1-two-source-zto-v1'
MAX_BYTES = 100000
SELECTORS = ('0x18160ddd', '0x313ce567')


class AgreementError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AgreementError(message)


def rpc_read(source, method, params, timeout):
    require(source in SOURCES, 'unrecognized public RPC source')
    P['validate_request'](method, params)
    require(type(timeout) in (int, float) and 0 < timeout <= 60,
            'timeout must be within (0, 60] seconds')
    body = P['canonical']({'jsonrpc': '2.0', 'id': 1,
                           'method': method, 'params': params})
    request = urllib.request.Request(
        source, data=body, method='POST',
        headers={'User-Agent': 'Pepeolithic-Line1-TwoSourceZTO/1.0',
                 'Content-Type': 'application/json',
                 'Accept': 'application/json',
                 'Accept-Encoding': 'identity'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                         B['NoRedirect']())
    try:
        with opener.open(request, timeout=timeout) as response:
            require(response.status == 200, 'RPC HTTP response was not 200')
            raw = response.read(MAX_BYTES + 1)
            require(len(raw) <= MAX_BYTES, 'RPC response exceeds byte limit')
            content_type = response.headers.get('Content-Type', '')
    except urllib.error.HTTPError as exc:
        raise AgreementError('RPC HTTP error ' + str(exc.code)) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AgreementError('RPC transport failed') from exc
    answer = B['parse_json'](raw)
    B['validate_response'](answer)
    read = {'method': method, 'params': params, 'content_type': content_type,
            'response': answer, 'response_sha256': P['digest'](answer)}
    P['validate_read'](read)
    return read


def validate_bundle(bundle):
    require(isinstance(bundle, dict) and set(bundle) ==
            {'schema', 'captured_at_utc', 'sources', 'transcript_sha256'},
            'bundle fields differ from schema')
    require(bundle['schema'] == SCHEMA, 'unknown bundle schema')
    stamp = bundle['captured_at_utc']
    require(isinstance(stamp, str) and len(stamp) <= 64,
            'invalid capture timestamp')
    try:
        moment = datetime.fromisoformat(stamp)
    except ValueError as exc:
        raise AgreementError('invalid capture timestamp') from exc
    require(moment.utcoffset() is not None and
            moment.utcoffset().total_seconds() == 0,
            'capture timestamp must be UTC')
    sources = bundle['sources']
    require(isinstance(sources, list) and len(sources) == 2,
            'expected exactly two source transcripts')
    require(bundle['transcript_sha256'] == P['digest'](sources),
            'transcript checksum mismatch')
    observations = []
    for index, source in enumerate(sources):
        require(isinstance(source, dict) and set(source) ==
                {'rpc_url', 'reads', 'reads_sha256'},
                'source fields differ from schema')
        require(source['rpc_url'] == SOURCES[index],
                'source labels are missing or reordered')
        reads = source['reads']
        require(isinstance(reads, list) and len(reads) == 4,
                'expected four ordered reads per source')
        require(source['reads_sha256'] == P['digest'](reads),
                'source checksum mismatch')
        results = [P['validate_read'](read) for read in reads]
        chain, block, supply, decimals = reads
        require(chain['method'] == 'eth_chainId' and chain['params'] == [] and
                results[0] == '0x1', 'source did not report Ethereum mainnet')
        require(block['method'] == 'eth_getBlockByNumber' and
                block['params'] == (["finalized", False] if index == 0 else
                                    [observations[0][0], False]),
                'block request is not the chosen finalized height')
        number, block_hash = P['block_identity'](results[1])
        if index:
            require((number, block_hash) == observations[0][:2],
                    'sources reported different blocks at the chosen height')
        pin = {'blockHash': block_hash, 'requireCanonical': True}
        for read, value, selector in zip((supply, decimals), results[2:], SELECTORS):
            require(read['method'] == 'eth_call' and
                    read['params'] == [{'to': P['ZTO'], 'data': selector}, pin],
                    'state read was not hash-pinned to ZTO')
            require(isinstance(value, str) and P['HASH'].fullmatch(value),
                    'state result is not one ABI word')
        raw_supply, places = int(results[2], 16), int(results[3], 16)
        require(places <= 255, 'decimals result exceeds uint8')
        observations.append((number, block_hash, raw_supply, places))
    require(observations[0] == observations[1],
            'sources disagree about ZTO supply or decimals')
    number, block_hash, raw_supply, places = observations[0]
    digits = str(raw_supply).rjust(places + 1, '0')
    tokens = digits if places == 0 else digits[:-places] + '.' + digits[-places:]
    return {'status': 'two_sources_agree_on_hash_pinned_zto',
            'block_number': P['quantity'](number), 'block_hash': block_hash,
            'zto_address': P['ZTO'], 'total_supply_raw': str(raw_supply),
            'decimals': places, 'total_supply_tokens': tokens,
            'sources': list(SOURCES),
            'transcript_sha256': bundle['transcript_sha256'],
            'evidence': 'Provider observations, not a consensus or state proof'}


def capture(timeout=15, read=None):
    read = rpc_read if read is None else read
    first = SOURCES[0]
    second = SOURCES[1]
    a_chain = read(first, 'eth_chainId', [], timeout)
    require(P['validate_read'](a_chain) == '0x1', 'first source is not mainnet')
    a_block = read(first, 'eth_getBlockByNumber', ['finalized', False], timeout)
    number, block_hash = P['block_identity'](P['validate_read'](a_block))
    b_chain = read(second, 'eth_chainId', [], timeout)
    require(P['validate_read'](b_chain) == '0x1', 'second source is not mainnet')
    b_block = read(second, 'eth_getBlockByNumber', [number, False], timeout)
    require(P['block_identity'](P['validate_read'](b_block)) ==
            (number, block_hash), 'sources reported different blocks')
    pin = {'blockHash': block_hash, 'requireCanonical': True}
    pairs = []
    for url, chain, block in ((first, a_chain, a_block),
                              (second, b_chain, b_block)):
        reads = [chain, block]
        for selector in SELECTORS:
            reads.append(read(url, 'eth_call',
                              [{'to': P['ZTO'], 'data': selector}, pin], timeout))
        pairs.append({'rpc_url': url, 'reads': reads,
                      'reads_sha256': P['digest'](reads)})
    bundle = {'schema': SCHEMA,
              'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'sources': pairs, 'transcript_sha256': P['digest'](pairs)}
    return bundle, validate_bundle(bundle)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--capture', metavar='OUTPUT',
                        help='save a new public-read transcript')
    action.add_argument('--verify', metavar='FILE',
                        help='replay a saved transcript offline')
    parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args(argv)
    try:
        if args.verify:
            raw = SAFE['read_bytes'](args.verify, MAX_BYTES)
            result = validate_bundle(B['parse_json'](raw))
        else:
            SAFE['parts'](args.capture)
            bundle, result = capture(args.timeout)
            raw = (json.dumps(bundle, indent=2, sort_keys=True,
                              allow_nan=False) + '\n').encode()
            SAFE['write_bytes'](args.capture, raw, MAX_BYTES)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (AgreementError, P['PinnedError'], B['SnapshotError'],
            OSError, ValueError, RecursionError) as exc:
        print('two-source-zto: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
