# JSON source report guard

Before using a saved violation's byte offsets to edit a JSON handoff, check that
its contract and document still have exactly the captured bytes, and reproduce
all diagnostics with the inherited validator. This catches stale locations,
altered ranges, removed errors and changed previews. The caller explicitly
names all three files; paths inside the report never select files to read.

From the repository root, one offline command reviews the real inherited report:

```sh
python3 -B line-2/tools/source-guard/review.py line-2/tools/source-locator/invalid-report.result.json line-2/tools/json-contract/report.contract.json line-2/tools/rule-locator/report.invalid.json
```

Observed: exit 0, `matches: true`, `status: report_reproduced`,
`document_valid: false`, and all three structural violations reproduced.
Exit 0 means the report matches, including a report about an invalid document;
it does **not** mean the document satisfies its contract.

An optional `--report-sha256 DIGEST` checks an independently retained SHA-256
before opening contract or document inputs. A mismatched pin exits 1 with
`report_pin_mismatch`. For the unchanged inherited report, the digest observed
here is `7b4836b1c3ae869758d1f54916f96be5dead4947755c553200ee9be3ffe14c8a`.
This published demonstration digest is illustrative, not independent approval.
To make a new saved report, run `source-locator/locate.py CONTRACT DOCUMENT`
and capture its stdout, including when it exits 1 for structural violations.
Batch reports and input-error reports are not supported by this guard.

Exit 1 means a pin, source identity or reproduced diagnostic mismatch. Exit 2
means an unreadable/malformed input, invalid contract or unsupported report.
Identity includes the exact workspace-relative path, byte count and SHA-256;
renaming a file also requires a new report. Report JSON formatting may change
unless its exact bytes are pinned. Diagnostic tree comparison preserves scalar
types, so a boolean cannot replace an integer coordinate. Missing-field anchors,
Unicode columns and original CRLF bytes retain source-locator semantics.

```sh
python3 -B line-2/tools/source-guard/test_review.py
```

All 18 regressions passed: unchanged valid and invalid reports, byte changes in
both sources, range/preview/type/order alterations, omitted diagnostics, missing
field anchors, pin checking before document access, malformed JSON, duplicate
keys, symlink refusal, and embedded paths that are never opened. Initial test
fixtures used absolute temporary paths; they were corrected to workspace-relative
paths to exercise the inherited boundary. Production behavior did not change.

Python 3.10+ standard library on POSIX is sufficient. Keep the existing
`source-locator`, `rule-locator`, `bounded-contract` and `json-contract` folders
beside this folder. The fixed bootstrap is reused from source-locator; trusted
sibling code is loaded through no-follow reads. Inputs are visible relative
workspace regular files, capped at 1 MB each, with symlinks refused. The command
writes only stdout and makes no network, environment, secret or wallet access.

A checksum and reproducible report authenticate no author, truth or business
policy. Replacing both files and their unpinned report can pass. The check
observes captured bytes; files may change again afterwards. Existing regex,
uniqueness, indexing and diagnostic work are not a CPU/memory sandbox. Contracts
and sibling Python code must be trusted. No coin or chain access is needed.
