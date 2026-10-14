# Anchor bridge

Check every provider-observed Ethereum parent link between two explicit retained
block anchors, with a caller-selected limit of at most 64 links. This fills a
small gap in the existing settlement tools: different-height anchor agreement
alone does not establish ancestry. It is Python 3.9+ using only the standard
library, with no installation, credentials, wallet, signing or transaction sending.

Run this command from the repository root to see the saved real-chain example:

```sh
python3 -B line-3/tools/anchor-bridge/bridge.py --demo
```

When tried, both public collection and offline replay returned
`observed_ancestry_connected`, exit 0, with **11 links checked** and no alerts.
The lower anchor is inclusion block **26190898** of real ZTO transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`,
with hash `0x92fd5a2a4e348630cc5e93252669b754760ae4e818a976dd00db145e30ddc8dd`.
The upper anchor is block **26190909**, hash
`0xa5ca989059d9515c55fc98b5d40200656e7dcb3f8e9781d43d486eddcd2b3cdc`.
These are historical blocks freshly read from Publicnode. `live-evidence.json`
contains the compact actual observations; `live-check.json` records the result.
The demo anchors are illustrative and bundled beside the evidence, not an
independently retained approval. The lower anchor was taken from the ancestor's
real ZTO paired settlement transcript; the upper was read at lower + 11, the
existing example's 12-confirmation threshold (inclusion counts as one).

## Explicit inputs

Choose and retain both anchors independently from submitted evidence. The JSON
shape is exactly `{"lower":{"number":INTEGER,"hash":"0xHASH"},
"upper":{"number":INTEGER,"hash":"0xHASH"}}`, with full 32-byte hashes.
Use the existing example to see the complete format. A fully explicit replay is:

```sh
python3 -B line-3/tools/anchor-bridge/bridge.py --anchors line-3/tools/anchor-bridge/demo-anchors.json --replay line-3/tools/anchor-bridge/live-evidence.json --max-links 11
```

To collect new observations of your retained anchors, replace `--replay PATH`
with `--live`. `--rpc` selects `https://ethereum-rpc.publicnode.com` (default)
or `https://eth.drpc.org`. Collection checks Ethereum chain ID 1, reads every
numeric block descending from upper to lower, and rereads both endpoints.
There are at most 68 public reads: one chain ID, 65 headers and two rereads.
No timers, polling, fallback, logs scan or transaction submission are involved.
The transport uses an explicit User-Agent, disables environment-derived proxies,
refuses redirects, bounds each response to 4 MB and each read to 20 seconds.
The CLI prints the result and compact sample; it writes no files.

Inputs must be visible workspace-relative regular JSON files, at most 90 KB.
The inherited safe reader refuses hidden/parent paths, absolute paths, symlinks,
duplicate JSON keys and nonfinite values. Anchors and budget are validated before
opening replay evidence or constructing a transport. Invalid or oversized
intervals never silently shorten the walk. Same-height identical anchors work
with zero links checked; conflicting same-height anchors fail.

Replay requires exact envelope/header keys, source label, Ethereum chain ID,
complete ordered contiguous headers, unique block hashes, both expected endpoint
hashes, every child parentHash equal to the previous block hash, and unchanged
endpoint rereads. No saved acceptance flag is trusted. Exit **0** means the
observed interval connects; **1** means changed endpoints or disconnected
observations require review; **2** means invalid input or an unavailable read.
Output is capped at 100 KB.

## Verification and limits

```sh
python3 -B -m unittest discover -s line-3/tools/anchor-bridge -p 'test_*.py' -v
```

All **25 tests passed**. They use the real saved interval and mutate copies in
memory to exercise middle-link failure, changed anchors/rereads, duplicate hashes,
wrong heights/order, missing/extra headers, exact budgets, invalid source/chain,
null provider results and input refusal before transport construction. Collection
request order and round-trip replay are checked without network.

This folder reuses unchanged `payment-witness/witness.py` and
`settlement-check/settlement.py`; keep those sibling folders when copying it.
No other folders are needed for its saved demo.

This is a component for settlement review, not a payment acceptance decision.
Combine it with the existing receipt execution, canonicality, confirmation,
finality and payment-policy checks. The short demo does not walk to the finalized
head or current head and does not establish present settlement. The parentHash
fields and block hashes are provider assertions; header hashes are not recomputed
and full Ethereum headers are not retained. Consistently forged observations
can pass. A source label authenticates no provider or independent operator, and
endpoint rereads cannot guarantee that the entire chain was atomic or prevent a
later reorganization. There is no receipt proof, ownership check or ledger.
