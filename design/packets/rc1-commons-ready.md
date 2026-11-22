# Packet rc1-commons-ready: commons' gate is green with its records gone, in both states

| item | value |
|---|---|
| from | agentik-hq's brief rc1-commons-ready, on design/28 and the ledger's entry 63; level S3 |
| pin | agentik-commons main 3567092 (suite 0.7.42); worktree `.claude/worktrees/rc1-commons-ready`, branch `rc1-commons-ready`; nothing linked from main |
| wall | this worktree, and a scratch clone with the holder's copy in a scratch folder outside every checkout; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test reads the live home or state; made-up names in fixtures; nothing under `plugins/`; `scripts/records-cut` never with `--go` |
| may touch | `tests/*.py` (a fixture or a helper only, no assertion changed, weakened or skipped), this packet, `history/sittings/*.md` |
| verify | `agentik records` in each rehearsal's clone; `make check` in the scratch clone for each rehearsal and once, last, in this worktree, each through the gate queue; `scripts/hygiene --require-private` and `--require-private --commits main..HEAD` |
| acceptance | 1 to 4 below |

## 1. The owner's words

The ledger's entry 63: "Each of agentik's public tools keeps its working records in agentik-hq. As a tool's row lands, its charters, packets, wish list and questions move to agentik-hq/repos/<tool>/ and leave the public tree in one commit; what is already pushed stays in the public history (design/28)." Its entry 37: "Never commit. The tool repos are public. Commit no hostname, address, email, person's name, account detail, or private repo's name or path; examples use made-up names."

A move of another tool, unrehearsed, turned 31 of its tests red: a test that runs a verb on a folder inside the clone reads the clone's records state, which no count of the tests that read a record file finds. So commons is rehearsed before it moves, in the two states a clone can be in after the move.

## 2. Rulings

- R1, the scratch clone: a `git clone` of this branch in a scratch folder, a local `main` at `origin/main`; `git rm -r` of every tracked path under the record names that exists (at the pin: `history/`, `design/packets/`, `NICE_TO_HAVE.md`; no `bugs/`, `HANDOFF.md`, `OPEN-QUESTIONS.md` or `relay/queue.yaml`); the line `records: out` added to `.hygiene-allow`; one commit in the scratch clone alone. The removed records kept in a second scratch folder, each at its own path, as the holder's copy.
- R2, the first rehearsal, no key: `agentik records` in the scratch clone (expected `state: unset`), then its whole `make check` through the gate queue.
- R3, the second rehearsal, the key `agentik.records` set in the scratch clone's own config to the holder's copy: `agentik records` (expected `state: out`), then its whole `make check` again through the gate queue.
- R4, a red: a test or a script that reads a record of its clone, or the clone's records state through a folder inside it or its working folder, is mended in tests alone (a fixture under `tests/`, or a copy in a temp folder outside every repository), no assertion changed, one commit each, a line in section 4; then a fresh clone and the red rehearsal again. A red where the suite's own code is wrong in a repo whose records are out stops the row as a finding; nothing under `plugins/` changes for it. Any other red is run once more and both are reported.
- R5, what stands: nothing under `plugins/` moves, so no version moves; in this worktree, which holds its records, every verb and test reads as at the pin.

## 3. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | R2: `make check` green on the scratch clone's head through the gate; `agentik records` there prints `state: unset` | not run; a clone holding its records prints `state: own` |
| 2 | R3: `make check` green on the scratch clone's head with the key set; `agentik records` prints `state: out` | not run |
| 3 | each red on the way: its test, its cause in one line, the commit that mends it, or "nothing turned red" | not run |
| 4 | `make check` in this worktree green through the gate; `scripts/hygiene --require-private` and `--commits main..HEAD` at 0 hits | green at sc15's landing; both scans 0 hits |

## 4. Findings

- None yet.
