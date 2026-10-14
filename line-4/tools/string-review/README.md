# Offline EIP-712 string reviewer

Show the exact UTF-8 bytes actually committed by every reachable `string` in
an EIP-712 domain and message. This helps a worker spot strings that look alike
but hash differently. Python standard library only; copy this whole folder to
use it offline. There are no runtime dependencies, configuration or network calls.

Run from the repository root:

```sh
python3 -B line-4/tools/string-review/string_review.py line-4/tools/string-review/zto-payment.json --expect 0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774
```

Tried: exit **0**, `matchesExpected: true`, `needsReview: false`. The unchanged
historical example commits to real Ethereum ZTO at
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`, transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`, and
**166357571280020680094504** raw units. It is inherited evidence, not a fresh
chain read, current payment, invoice, permit or claim of contract support.
The saved expected digest demonstrates execution; obtain an independent
expected digest for a real request.

Replace `zto-payment.json` with `zto-hidden-space.json` in that command to see
exit **1**, a digest mismatch and a review cue for **U+200B ZERO WIDTH SPACE**
at `/domain/name`, scalar index **17**, UTF-8 byte offset **17**. This second
fixture deliberately inserts one invisible character in the historical domain
name. It is a mutation demonstration, with every other value unchanged.
Both complete local reports are in `example-zto-*.json`.

Input is the exact typed-data object with `types`, `primaryType`, `domain` and
`message`, rather than a JSON-RPC envelope. Output gives the complete digest,
domain/message hashes, each signed string's JSON Pointer, exact value, UTF-8
hex, scalar and byte lengths, and Keccak-256 field word. Cues list zero-based
Unicode scalar indexes, zero-based UTF-8 byte offsets, code points, names,
categories and bidirectional classes. UTF-8 byte offsets are not UTF-16 indexes
or grapheme positions. Strings inside nested structs and arrays are included;
`bytes`, hex addresses, integer spellings and unreachable type declarations
are not interpreted as signed strings.

Review cues cover every non-ASCII scalar, Unicode C categories (controls,
formatting, private use and unassigned characters), M categories (marks),
non-ASCII separators, and whitespace at either edge. Interior ASCII spaces
are unflagged; tabs and newlines are controls. Legitimate non-ASCII language
and emoji also request review. Cues are observations, not a malware verdict.
This is not a confusable-character database or a complete Unicode security
policy: font appearance, ASCII lookalikes, grapheme boundaries, script mixing
and renderer behavior are not resolved. No cues does not mean safe to sign.

When NFC or NFKC normalization would change a string, the report shows that
alternative's exact value, UTF-8 bytes and field word. **It never normalizes,
trims or rewrites input before hashing**, and does not treat normalized equality
as signed-byte equality. These are per-field alternatives, not replacement
whole-message digests. Reports identify Python's Unicode database version;
classification/normalization cues may differ across Python releases, while
the original bytes and digest remain unchanged. All CLI JSON and error messages
escape non-ASCII and control characters for terminal display. A consumer that
decodes and renders raw strings must choose its own safe display treatment.

Exit **0** means no review cues and a matching expected digest if supplied.
Exit **1** means review cues or an expected-digest mismatch. Exit **2** means
invalid input, unsafe file access, or exceeded bounds; no partial JSON report
is emitted. Omitting `--expect` calculates without an independent comparison.
The command writes no files and never signs, sends, pays, posts or touches
keys, wallets, secrets or environment variables.

The unchanged ancestor encoder and file reader validate first: strict UTF-8
JSON, no duplicate keys/floats/nonfinite values, at most 65,536 input bytes,
48 nesting levels, 8,192 nodes, 64 types, 256 fields and eight array dimensions.
Files must be regular no-follow files beneath cwd; hidden paths, parent
traversal and symlinks are refused. POSIX directory descriptors are required.
The entire ASCII JSON report, including newline, is capped at **100,000 bytes**.
An oversized report is refused rather than truncating a signed value. Bounds
limit size; they do not guarantee a CPU budget. The inherited encoder is not
an independent second cryptographic engine or a newly audited implementation.

```sh
python3 -B -m unittest discover -s line-4/tools/string-review -v
```

Tried: **20 tests passed**, covering exact historical ZTO digest, invisible and
bidirectional characters, UTF-8 offsets after astral scalars, NFC/NFKC differences,
legitimate non-ASCII text, controls, whitespace, variation selectors, nested
arrays, absent strings, invalid data, duplicate keys, output bounds and CLI
exits. The **28 ancestor tests** passed from scratch, including published
Keccak/Ether Mail vectors and file-boundary checks. A detached copy passed all
20 new tests and the ZTO CLI without sibling tools or packages.

Unchanged source/fixture hashes are in `provenance.json`. Encoding follows
[EIP-712](https://eips.ethereum.org/EIPS/eip-712), which hashes dynamic string
contents; names, categories and normalization come from Python's standard
[`unicodedata`](https://docs.python.org/3/library/unicodedata.html). Neither
digest equality nor these cues establish identity, consent, ownership,
settlement, replay protection or approval.
