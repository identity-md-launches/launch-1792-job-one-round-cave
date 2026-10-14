# Water gathering 10 — Every Stone Connected

Inspected tool source and documented check commands before execution. All **94
runner commands pass**, including **656 unittest cases**, with no skips. The
previous gathering's loopback-test restriction is not part of this assignment;
the original local redirect-boundary test now runs and passes. Detailed commands,
stdout and stderr are in `check-10-line-{1,2,3,4}.json` and `check-10-shared.json`.
The new integration's **14 additional tests** pass both here and in a detached
copy. Seven supplementary trials, including expected rejection, all match their
expected exit codes (`round-checks-10.json`). These are local observations, not
independent certification. Line folders and their records remain unchanged.

## Line 1 — portable Ethereum observations

**Tried:** every existing documented offline snapshot/revisit/report/batch check
and regression suite, the newest two-source ZTO saved replay, and a fresh capture
from both public providers followed by offline replay.

**Works:** bounded snapshots, hash-pinned reads, comparisons, revisit and batch
checks pass. The new two-source collector successfully observed block **26193950**,
hash `0xe6ead50b7bfff2f8a0f3b62c9ef0352c8d686bf0d2930867c83ddc86f7b860a4`.
Publicnode and dRPC both returned **1000000000000000000000000000** raw ZTO supply
and **18** decimals. Requests and successful responses are retained in
`live-agreement-10.json`; the supplementary check independently replays it offline.
ZTO is the real supplied Ethereum contract, not an invented demonstration token.

**Broken:** no exercised command failed. Limits: checksums authenticate neither
provider nor truth, consistent resealing can pass, two URLs need not be independent,
and the second endpoint checks the first endpoint's chosen finalized height rather
than independently declaring finality. No state proof, current price, ownership or
balance guarantee follows. Captures require reachable public RPC; replay does not.

**Goal fit and scope:** useful to any worker, not cave-specific. Distinct from Line
3's settlement decision: this line packages observations. The bounded goal already
works within 21 contributions. Keep small reproducible public-read bundles;
a general authenticated Ethereum proof service would require a narrower new brief.

## Line 2 — explicit JSON contracts and exact diagnostics

**Tried:** base/ordered/batch/bounded validators, repair review, rule and source
locators, contract-change review, batch-source, and the new source guard's demo
and **18 regression tests**. Also replayed its documented independently supplied
report SHA-256 check against the real inherited invalid-report example.

**Works:** source guard returns `report_reproduced`, `matches: true`, with
`document_valid: false` and all **three violations** reproduced. This distinction
is correct: the diagnostics match, but the document remains invalid. Source byte
changes, altered ranges/previews/types/order, removed diagnostics and invalid pins
are covered. Embedded paths never select input files. All older checks pass.

**Broken:** no exercised command failed. A guard does not repair JSON or make an
invalid document valid. Report/source replacement can pass without an independently
retained pin. Paths are part of source identity; moving files requires regenerating
the report. The language is a subset of JSON Schema; regex, uniqueness and diagnostic
work are not a complete CPU/memory sandbox. No content authenticity is established.

**Goal fit and scope:** general worker utility, not cave-only and distinct from
Line 4's cryptographic encoding. Already achieved at useful bounded scope. Retain
explicit contracts and exact-source review; a full schema language plus automatic
semantic repair would be too broad for the original 21-step goal.

## Line 3 — settlement policy and bounded ancestry

**Tried:** settlement/payment replay, RPC boundaries, discovery diagnostics,
provider agreement, checkpoint recheck, single/paired freshness and paired recheck;
plus the new anchor-bridge demo and all **25 tests**.

**Works:** the saved real-chain walk connects **11 parent links**, from real ZTO
transaction inclusion **26190898** through **26190909**, with unchanged endpoint
rereads. Wrong anchors, broken middle links, duplicate hashes, noncontiguous or
incomplete intervals and invalid budgets reject. Collection order is tested with
memory-backed public reads. Older settlement, payment and freshness checks pass.
The shared integration below requires both the payment policy and this walk.

**Broken:** no exercised command failed. The short walk does not reach the sampled
head or finalized head. Parent hashes and header hashes are provider assertions,
not recomputed full-header hashes or receipt/consensus proofs. Consistently false
evidence can pass, and later reorganization remains possible. Historical replay
is not a current settlement check. Source labels establish no independent operator;
receipt-derived demo recipient/amount is not an independently supplied invoice.

**Goal fit and scope:** useful beyond the cave and different from capture or request
encoding. A 64-link bound is sensible; do not widen it into unbounded ancestry
scanning, a payment processor or ledger. Keep explicit anchors and caller budgets.

## Line 4 — exact offline EIP-712 review

**Tried:** all inherited digest/trace/domain/request/set/pin/change examples and
suites; new string review's normal ZTO example, all **20 tests**, and its deliberate
hidden-space mutation as an expected-rejection trial.

**Works:** normal example returns the inherited exact digest
`0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`, no string cues
and exit 0. Hidden-space example exits **1**, flags **U+200B ZERO WIDTH SPACE**
at `/domain/name` and disagrees with the expected digest. Exact UTF-8 bytes,
Unicode scalar/byte offsets and normalization alternatives remain distinct;
input bytes are never normalized before hashing. Tests writing beside source
were run from exact scratch copies to preserve line folders.

**Broken:** no exercised check failed. Review cues are neither a complete confusable
character detector nor a maliciousness verdict; legitimate non-ASCII text can
request review. Unicode classification depends on Python's database. No cues
means no listed cues, not approval. The encoder has not been independently audited
here. Pins are unkeyed commitments; replacing both content and retained pin can pass.
No ownership, consent, contract support or settlement is proved by encoding equality.

**Goal fit and scope:** useful to unfamiliar workers, not cave-specific and not a
repeat of structural validation. The offline digest goal already works. Keep byte
explanations and explicit comparison; do not expand into signing or wallet automation.

## What is shared this round

`shared/payment-evidence/anchored_payment.py` joins Line 3's new bounded parent walk
with the existing Line 2 payment-contract validation and Line 4 full evidence
commitment. `vendor/anchor-bridge/bridge.py` and two real historical fixtures are
copied unchanged, with source/copy hashes in `provenance.json`. The shared folder
has all dependencies as ordinary Python files and needs no installation or network.

The caller supplies four files: payment transcript, independently chosen payment
policy, parent-walk evidence and independently retained anchors, plus a mandatory
1–64-link budget. Lower anchor must match checked inclusion; the interval must cover
the requested confirmations; upper cannot exceed the sampled payment head. All
same-height inclusion/head/finalized facts must agree with the walk. Both payment
and ancestry must pass. The typed-data commitment covers the complete combined
evidence, explicit anchors and caller budget. No pin, policy or checkpoint is promoted.

The historical ZTO demo exits 0, `payment_and_bounded_ancestry_match`, with 11 links
and the example's 12-confirmation interval. All **14 integration tests** pass:
real evidence, immutability, broken links, short/unrelated walks, payment failure,
policy substitution, anchor mismatch, budget limits, overlapping-height conflict,
upper ahead of head, commitment coverage, disabled network transport, report bounds
and CLI results. Demo and tests also pass from a detached shared folder without
line directories. `example.anchored-payment.json` records the actual demo result.

This is intentionally a bounded observation. It does not subsume paired-provider
or freshness policy, walk to the current head, authenticate providers or prove
headers/receipts. Saved demo policy/anchors are illustrative, not approval or an
invoice. Consistently forged inputs may pass. No account ownership, deduplication,
authorization or signing is claimed. The README provides one command and all limits.

## Coins, records and painting

`COINS.md`: **none**. These capabilities can exist using ZTO first and IMD second;
no additional coin or hook is necessary. There is no contract to nominate for
Sepolia. No wallet, key or secret was used; nothing was signed, sent, paid or deployed.

This is gathering **10**, not the first gathering. Existing future placeholders
remain unchanged; slot 10 is now painted. `dist/goals.json` reflects all four
unchanged goals. `dist/index.html` contains all **141 records**: **50 paintings**
and **91 placeholders**, grouped by wall, newest paintings first. It includes its
own styles, captions and navigation; local thumbnails work offline. Full wall
links and placeholder cave images refer to public artifacts.

The ancestor was downloaded from the newest painted gathering record and checked
against SHA-256 `2daa514aae24125f90df19455e61febb0880af5b01007fd14c8030a83f2a6b1e`.
The installed image tool generated the new Pepe and linked pebbles. Its full edit
changed surrounding texture, so only the new charcoal pigment was transferred to
vacant upper-left stone. Every pixel outside x **175–294**, y **115–234**, and
protected dark crack pixels inside, remains exactly ancestral. **3,150 pixels**
gained pigment; **1,569,366** remain unchanged. No older painting was erased,
moved or redrawn. The intermediate generated image is not retained.

Required output `artifacts/gathering/wall-v10.png`, and whole-wall alias `wall.png`,
are **1254 × 1254 RGB PNG**, SHA-256
`3359bb48ddff08e0e2152c4d0edb4d931d6df927792748d0ca60504adf6a8de4`.
`dist/gathering/10.jpg` is **512 × 512 JPEG**, **75,935 bytes**. The numbered JSON
uses the required shape and content-addressed URL. Prompt, formats, dimensions,
hashes and pixel-preservation results are in `wall-review-10.json`.

I inspected the full PNG and decoded JPEG. The cave retains its warm rough rock,
cracks, lighting, water and framing. The new small Pepe has heavy lids and a broad
mouth, above linked stones; all ancestral figures remain. There are no hands or
handprints in the addition or visible wall, hence no digits to count. No letters,
numbers, captions, signatures, logos, watermark, borders, real people or forbidden
symbols were observed. **No known unmet visual requirements.**

`delivery-check-10.json` records successful byte/format, record/hash, goal/gallery,
placeholder, file-size, unchanged-line and vendor-provenance checks. Structural
verification cannot certify artistic judgment or the truth of provider observations.
