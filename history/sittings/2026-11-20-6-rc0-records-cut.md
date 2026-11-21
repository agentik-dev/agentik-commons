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
| P2 the phase 2 | done: `git merge main` (65e15b8); NICE keeps main's rows and sections, then this row's: n261 to n271 are now n267 to n277 (build 1's n261 and n262 to n267 and n268, under a new "From row rc0-records-cut (build 1)"; review 1's n263 to n268 to n269 to n274; review 2's n269 to n271 to n275 to n277), in the packet too (the pin, and `.hygiene-allow` in may touch); the overflow keeps rr7's section of n191 to n194 and n200 to n202, then this row's n203 and n205 to n208; n209, n210, n211 and n213 to n215, the next oldest S4, to the overflow for the bound (24,456 B, 65 rows); `test_up2_suite_origin.py` is main's; no file under `plugins/` differs from main, so no version |
| V recordlint, the tests, hygiene, the gate | not done |

Build 3's acts (the proof after the copy, the remotes by host and path, `.hygiene-allow` as git compares it, the words, the NICE rows) are as its record says; build 4 changes none of them.

## Next act

The checks: recordlint, `tests.test_records_cut` and `tests.test_up2_suite_origin`, hygiene on the tree and `main..HEAD`, then `make check` once through the gate queue.

## Handover

- None open. Build 3's allow-row line is settled by brief 4: the row is in.
- The older charters of this row (`-2`, `-5`) keep the numbers they wrote then; the map above holds.

## Exit

Open.
