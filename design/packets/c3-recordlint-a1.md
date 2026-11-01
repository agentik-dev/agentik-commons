# Packet c3, amendment 1: refuter round 1's F1, and three cheap S4s

| item | value |
|---|---|
| from | c3's refuter round 1 (FAIL on F1, S3), sitting 2026-11-01-2-hq; the packet `design/packets/c3-recordlint.md` |
| pin | branch `c3-recordlint` at b54c807, worktree `~/code/agentik-commons/.claude/worktrees/c3-recordlint`; continue there |
| wall, may touch, verify | the packet's rows, unchanged; may touch adds nothing beyond `scripts/recordlint`, `tests/test_recordlint.py`, `NICE_TO_HAVE.md`, this amendment as `design/packets/c3-recordlint-a1.md`, the charter |
| budget | One commit per act. **Stop at 60k context or 40 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

Read first: this file; `scripts/recordlint` whole; `tests/test_recordlint.py`; `~/code/agentik-decisions/plugin/lib/decisions/backlog.py:270-285`.

## Acts

0. This amendment, committed first, as `design/packets/c3-recordlint-a1.md`.
1. **F1 (S3, blocks).** `scripts/recordlint:117-121` compares `#` as text, so `| 1 |` and `| 01 |` pass as two numbers while `backlog.py:278` reads both as step 1. Under `number`, a `#` cell is `^[1-9][0-9]*$`: a leading zero is red. Tests: `01` reds `number`; `1` twice still reds the duplicate.
2. **Byte ceilings at the edge.** GUIDE §4 tests a byte ceiling at it: NICE at exactly 24,576 B reds and 24,575 passes; HANDOFF at exactly 8,192 B reds and 8,191 passes.
3. **An unreadable file** is one finding line `path:0: unreadable: <reason>`, exit 2, never a traceback. A test (a `chmod 000` file under a temp dir, skipped when running as root).
4. **NICE rows.** n3's `finding` cell is reworded so `backlog` titles it by what is unchecked, not "not checked:". New rows, S4, ids from n4: README's `make check` line names no recordlint (hq's decision, rides commons' next packet); rule 1 skips a near-miss header in HANDOFF as well as NICE (fold into n2 instead if it reads better); a cell's `<br>` or list is not checked; bullets above the first `##` pass, though §2's shape is one head paragraph. recordlint green on the file.
5. The gate, last.

## Report (at most eight lines)

The sha; each act's commit; the gate's id and its code from its line; the suite's counts; the NICE ids added.
