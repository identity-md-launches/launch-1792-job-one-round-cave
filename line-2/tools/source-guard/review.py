#!/usr/bin/env python3
"""Reproduce a saved source-locator report before using its source coordinates."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import types

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module



def dependencies():
    reader = bounded_module()
    path = Path(__file__).absolute().parent.parent / 'source-locator' / 'locate.py'
    relative = path.relative_to(Path.cwd()).as_posix()
    source = types.ModuleType('guard_source_locator')
    source.__file__ = str(path)
    exec(compile(reader.read_bytes(relative), str(path), 'exec'), source.__dict__)
    _, engine, rules = source.dependencies()
    return reader, source, engine, rules


def exact(a, b):
    """JSON tree equality including scalar types (true cannot stand in for 1)."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def review(reader, source, engine, rules, report_name, contract_name,
           document_name, report_sha256=None):
    # Paths embedded in an untrusted report NEVER select files to open.
    raw = reader.read_bytes(report_name)
    digest = hashlib.sha256(raw).hexdigest()
    if report_sha256 is not None:
        if not re.fullmatch('[0-9a-f]{64}', report_sha256):
            raise ValueError('report SHA-256 must be 64 lowercase hex digits')
        if digest != report_sha256:
            return {'matches': False, 'status': 'report_pin_mismatch',
                    'report_sha256': digest}, 1
    saved = source.strict_json(raw.decode('utf-8'))
    if not isinstance(saved, dict) or not isinstance(saved.get('sources'), dict):
        raise ValueError('expected a successful single-document source-locator report')
    identities = saved['sources']
    if set(identities) != {'contract', 'document'}:
        raise ValueError('report must identify exactly one contract and document')
    contract = source.Source(reader.read_bytes(contract_name), contract_name)
    document = source.Source(reader.read_bytes(document_name), document_name)
    current = {'contract': contract.identity(), 'document': document.identity()}
    base = {'matches': False, 'report_sha256': digest, 'sources': current}
    if not exact(identities, current):
        return {**base, 'status': 'source_identity_mismatch'}, 1
    regenerated = source.locate(engine, rules, contract, document)
    if not exact(saved, regenerated):
        return {**base, 'status': 'diagnostic_mismatch'}, 1
    return {**base, 'matches': True, 'status': 'report_reproduced',
            'document_valid': regenerated['valid'],
            'error_count': regenerated['error_count']}, 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', help='saved single-document source-locator report')
    parser.add_argument('contract', help='explicit trusted contract path')
    parser.add_argument('document', help='explicit document path')
    parser.add_argument('--report-sha256', help='optional independently retained report digest')
    args = parser.parse_args(argv)
    try:
        report, code = review(*dependencies(), args.report, args.contract,
                              args.document, args.report_sha256)
    except (ValueError, OSError, RecursionError, KeyError, IndexError) as exc:
        report, code = {'matches': False, 'status': 'input_error', 'error': str(exc)}, 2
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
