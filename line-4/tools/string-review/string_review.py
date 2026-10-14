#!/usr/bin/env python3
"""Expose exact signed EIP-712 string bytes and Unicode review cues offline."""
import argparse
import json
import sys
import unicodedata as ud

from typed_digest import (ARRAY, TypedDataError, digest, keccak256,
                          load_workspace_json, parse_hex)

MAX_REPORT_BYTES = 100_000


def pointer(parent, part):
    return parent + '/' + str(part).replace('~', '~0').replace('/', '~1')


def string_detail(text, path):
    raw = text.encode('utf-8')
    cues = []
    offset = 0
    for index, char in enumerate(text):
        category = ud.category(char)
        reasons = []
        if ord(char) > 127:
            reasons.append('non_ascii')
        if category.startswith('C'):
            reasons.append('control_format_or_unassigned')
        if category.startswith('M'):
            reasons.append('combining_or_enclosing_mark')
        if category.startswith('Z') and char != ' ':
            reasons.append('non_space_separator')
        if char.isspace() and (index == 0 or index == len(text) - 1):
            reasons.append('edge_whitespace')
        if reasons:
            cues.append({'scalarIndex': index, 'utf8OffsetBytes': offset,
                         'codePoint': f'U+{ord(char):04X}',
                         'name': ud.name(char, '<unnamed>'), 'category': category,
                         'bidirectionalClass': ud.bidirectional(char),
                         'utf8Hex': char.encode('utf-8').hex(), 'reasons': reasons})
        offset += len(char.encode('utf-8'))
    alternatives = []
    for form in ('NFC', 'NFKC'):
        normalized = ud.normalize(form, text)
        if normalized != text:
            normalized_bytes = normalized.encode('utf-8')
            alternatives.append({'form': form, 'value': normalized,
                                 'utf8Hex': normalized_bytes.hex(),
                                 'word': '0x' + keccak256(normalized_bytes).hex()})
    return {'path': path, 'value': text, 'scalarCount': len(text),
            'utf8Bytes': len(raw), 'utf8Hex': raw.hex(),
            'word': '0x' + keccak256(raw).hex(), 'cues': cues,
            'normalizationAlternatives': alternatives,
            'needsReview': bool(cues or alternatives)}


def render(report):
    text = json.dumps(report, ensure_ascii=True, indent=2) + '\n'
    if len(text.encode('ascii')) > MAX_REPORT_BYTES:
        raise TypedDataError('string review exceeds 100000-byte output limit')
    return text


def review(data, expected=None):
    # Validate the complete schema and values before inspecting signed strings.
    hashes = digest(data)
    expected_bytes = parse_hex(expected, 32) if expected is not None else None
    strings = []

    def visit(kind, value, path):
        array = ARRAY.fullmatch(kind)
        if array:
            for index, child in enumerate(value):
                visit(array.group(1), child, pointer(path, index))
        elif kind in data['types']:
            for field in data['types'][kind]:
                visit(field['type'], value[field['name']], pointer(path, field['name']))
        elif kind == 'string':
            strings.append(string_detail(value, path))
            # Bound cumulative rendering rather than truncate any signed value.
            render({'strings': strings})

    visit('EIP712Domain', data['domain'], '/domain')
    visit(data['primaryType'], data['message'], '/message')
    report = {'reviewVersion': 1, **hashes, 'unicodeDatabaseVersion': ud.unidata_version,
              'strings': strings, 'stringCount': len(strings),
              'needsReview': any(item['needsReview'] for item in strings),
              'interpretation': 'Cues request human review; absence of cues is not approval. '
                                'Original UTF-8 bytes determine the digest. '
                                'Normalization alternatives are never substituted.'}
    if expected_bytes is not None:
        report['matchesExpected'] = expected_bytes.hex() == hashes['digest'][2:]
    render(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='typed-data JSON below cwd; max 65536 bytes; no symlinks')
    parser.add_argument('--expect', help='independently obtained exact 32-byte digest')
    args = parser.parse_args(argv)
    try:
        report = review(load_workspace_json(args.input), args.expect)
        print(render(report), end='')
        return int(report['needsReview'] or not report.get('matchesExpected', True))
    except (ValueError, OSError, RecursionError) as exc:
        print('string-review: ' + json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
