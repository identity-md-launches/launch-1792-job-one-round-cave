# Two-source ZTO agreement

This standard-library Python tool captures eight public Ethereum JSON-RPC reads
from two fixed endpoints. It selects the first endpoint's reported finalized
block, asks the second endpoint for that same height, and requires equal hashes.
Both endpoints then read the real ZTO contract's `totalSupply()` and `decimals()`
with the same EIP-1898 block hash and `requireCanonical: true`. The portable JSON
keeps the request methods and parameters, full successful responses, source labels, per-response
checksums and transcript checksum. Offline replay checks the block and values
agree, as well as the inherited strict response and file-boundary rules.

Run this one command from the repository root to see the included real-chain
observation working **without network access**:

```sh
python3 -B line-1/tools/two-source-zto/agreement.py --verify line-1/tools/two-source-zto/live-agreement.json
```

I captured `live-agreement.json` on 2026-10-14 UTC from
`https://ethereum-rpc.publicnode.com` and `https://eth.drpc.org`. Capture and
offline verification both exited 0. The providers reported block **26193822**,
hash `0x12449302b51c7c97a83dfb6de021ddab5bf4ed2a0e9ca6cc5ca29d6a6c96a944`,
ZTO raw supply **1000000000000000000000000000**, and **18** decimals. The saved
transcript is 36,796 bytes. Seven local mutation checks also passed; they
reject changed responses, resealed supply disagreement, wrong hash pin, changed
block, wrong chain and out-of-range decimals.

To capture a fresh observation into a **new** visible workspace file:

```sh
python3 -B line-1/tools/two-source-zto/agreement.py --capture test/scratch/my-agreement.json
```

Capture uses only public read methods. It sets its own User-Agent, refuses
redirects, disables environment proxy discovery and caps responses and the
saved file at 100,000 bytes. The output is published without replacing an
existing path; input replay refuses symlinks and nonregular files. These file
rules, the strict JSON parser and the ZTO request validator are reused from
the sibling `safe-snapshot-files`, `bounded-rpc-snapshot` and `hash-pinned-zto`
tools. Keep those ordinary repository files with this folder. No wallet, key,
signature, transaction, payment or new coin is involved.

Agreement means these two **reported** responses match. It is not an Ethereum
state proof, evidence that the endpoints have independent operators, or a
guarantee against future reorganization. The second endpoint is asked for the
first endpoint's reported finalized height; it does not independently assert
finality. Checksums catch accidental edits but not consistently forged and
resealed transcripts. Capture needs reachable public RPC endpoints; offline
verification does not. A provider that lacks EIP-1898 support causes capture to
fail rather than falling back to a weaker selector.
