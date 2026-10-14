#!/usr/bin/env python3
"""Check new bridge, independent rejections, live replay and a detached copy."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'shared/payment-evidence/'
DEMO = [BASE+'anchored_payment.py', BASE+'example.transcript.json',
        BASE+'example.policy.json', BASE+'anchor-evidence.json',
        BASE+'anchor-expectations.json', '--max-links', '11']


def main():
    assert Path.cwd() == ROOT
    detached = ROOT/'test/scratch/portable10'
    shutil.copytree(ROOT/BASE, detached/BASE, dirs_exist_ok=True)
    cases = [
        (ROOT, 0, [BASE+'test_anchored_payment.py']),
        (ROOT, 0, DEMO),
        (detached, 0, DEMO),
        (detached, 0, [BASE+'test_anchored_payment.py']),
        (ROOT, 0, ['line-1/tools/two-source-zto/agreement.py', '--verify', 'gathering/live-agreement-10.json']),
        (ROOT, 1, ['line-4/tools/string-review/string_review.py', 'line-4/tools/string-review/zto-hidden-space.json', '--expect', '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774']),
        (ROOT, 0, ['line-2/tools/source-guard/review.py', 'line-2/tools/source-locator/invalid-report.result.json', 'line-2/tools/json-contract/report.contract.json', 'line-2/tools/rule-locator/report.invalid.json', '--report-sha256', '7b4836b1c3ae869758d1f54916f96be5dead4947755c553200ee9be3ffe14c8a']),
    ]
    rows=[]
    for cwd, expected, args in cases:
        done=subprocess.run([sys.executable,'-B',*args],cwd=cwd,capture_output=True,text=True,
                            timeout=45,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'})
        rows.append(dict(command='python3 -B '+' '.join(args),
                    workingDirectory='.' if cwd==ROOT else str(cwd.relative_to(ROOT)),
                    expectedExit=expected,exitCode=done.returncode,passed=done.returncode==expected,
                    stdout=done.stdout,stderr=done.stderr))
        print('PASS' if rows[-1]['passed'] else 'FAIL',args[0],done.returncode)
    raw=json.dumps(rows,indent=2)+'\n'
    assert len(raw.encode()) <= 100000
    Path('gathering/round-checks-10.json').write_text(raw)
    return 0 if all(r['passed'] for r in rows) else 1

if __name__=='__main__':
    raise SystemExit(main())
