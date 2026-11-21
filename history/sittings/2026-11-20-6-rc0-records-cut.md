# Sitting 2026-11-20-6-rc0-records-cut: row rc0-records-cut, build 4, the phase 2 (builder)

| item | value |
|---|---|
| goal | build 4: the allow row that holds commit 169e93b's made-up remote URLs; the phase 2 behind main (hn1-help-next, rr7-way-in); this row's NICE rows renumbered after main's highest; no change to the script or its tests |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | branch tip d7bd1d2 (build 3's checked head); main 65e15b8, rr7-way-in's merge; nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; the script only on scratch fixtures |
| verify | recordlint, `tests.test_records_cut` and `tests.test_up2_suite_origin` directly; hygiene on the tree and `main..HEAD`; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| A the allow row | done: `tests/test_records_cut.py: email` under its reason, after rr2's row; the commit scan reads the range tip's `.hygiene-allow`, so it holds once committed |
| P2 the phase 2 | not done: the next act |
| V recordlint, the tests, hygiene, the gate | not done |

Build 3's acts (the proof after the copy, the remotes by host and path, `.hygiene-allow` as git compares it, the words, the NICE rows) are as its record says; build 4 changes none of them.

## Next act

The phase 2: `git merge main`; keep main's NICE rows and overflow, then this row's; renumber this row's rows after main's highest, in the packet and here; old S4 rows to the overflow if the bound needs; `tests/test_up2_suite_origin.py` is main's whole.

## Handover

- None open. Build 3's allow-row line is settled by brief 4: the row is in.

## Exit

Open.
