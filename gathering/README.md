# Water gathering 09

This round checks the four lines and adds a portable offline bridge between a
retained paired ZTO payment checkpoint and a pinned, explained EIP-712 request.
See `REPORT.md` for each line's working behavior, trials, limits and goal scope;
`COINS.md` says none. All line folders remain byte-for-byte unchanged.

The shared deliverable, its one-command historical demo and 12 integration tests
are documented in [the payment bridge README](../shared/payment-evidence/README.md#gathering-09-retained-checkpoint-and-explained-request-changes).
Copy the complete `shared/payment-evidence/` folder to use it without the lines,
packages or network. Its two retained pins must be independently established;
the saved demo pins and intended/client self-comparison are illustrative.

From the repository root:

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/check_round_09.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery.py
```

All 87 runner commands pass: 592 test cases pass and one is explicitly skipped.
The checks include the latest four line tools, the expected one-unit typed-data
rejection, a stricter-policy rejection, the fresh ZTO batch's offline replay,
the shared integration and a detached-folder trial. One inherited test requiring
an additional loopback server is explicitly skipped under the task's endpoint
restriction. Per-command output is saved in `check-09-*.json` and
`round-checks-09.json`. No checks sign or dispatch a request.

The fresh real ZTO observation is `live-batch-09.json`: finalized block 26193694,
one billion ZTO supply and 18 decimals. `live-batch-trial-09.json` records the
source and outcome. This is an RPC observation, not a state proof or current
price. `live_batch_09.py` accepts an explicit approved transport route; it does
not read environment settings and its evidence source remains the public URL.

The mark **Two Remembered Branches** adds a small heavy-lidded Pepe and a forked
twig joining two pairs of pebbles. The built-in imagegen tool generated the new
pigment; `finish_wall_09.py` composited it onto vacant ancestral stone with exact
outside-pixel and dark-crack preservation. Its one-time input was overwritten by
the finished wall. The PNG and JPEG were visually inspected; no known visual
requirements are unmet. No hands, handprints, text or prohibited symbols appear.

Deliverables: `artifacts/gathering/wall-v9.png` (also `wall.png`), **1254 × 1254
RGB PNG**; `dist/gathering/09.jpg`, **512 × 512 JPEG**; and `09.json`.
`wall-review-09.json` records the prompt, preservation, hashes, dimensions,
formats and review. The gallery holds 45 paintings and 92 pending slots.
The required PNG remains untracked for separate upload.

## Gathering 10

See `REPORT.md` for the latest four-line review. `run_checks.py` now runs all
94 inherited/current check commands. `check_round_10.py` exercises the new shared
anchored payment bridge, a detached copy, live ZTO replay and expected rejection.
`check_delivery.py` checks round 10 outputs and the unchanged line-source snapshot.

The installed image tool generated the small Pepe with linked stones. Only its
charcoal pigment was composited onto vacant ancestral rock; the generated full
edit was discarded. Final output: `artifacts/gathering/wall-v10.png` (1254 square
RGB PNG), alias `wall.png`, and `dist/gathering/10.jpg` (512 square JPEG).
`wall-review-10.json` records the prompt, hashes and visual inspection. No known
unmet visual requirements; no hands or handprints were added. The bridge remains
historical provider evidence, not a current payment or consensus proof.

One command to check the delivery from the repository root:

```sh
python3 -B gathering/check_delivery.py
```
