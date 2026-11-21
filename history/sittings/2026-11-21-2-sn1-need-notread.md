# Sitting 2026-11-21-2-sn1-need-notread: row sn1-need-notread, build 1 (builder)

| item | value |
|---|---|
| goal | packet `design/packets/sn1-need-notread.md`: a module need is met by any interpreter of one tuple; `not_read` names every part not read, and the screen says it once |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | main 2d96be7 (ak10c5-table-gone's merge); nothing linked from main |
| wall | this worktree; no push, amend, rebase, merge; no bare make; no relay verb; setup only `--dry-run` |
| verify | the touched tests directly; hygiene `--commits main..HEAD`; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| 1 the packet, measured at the pin | done |
| 2 R1: `plan.PYTHONS`, the walk, `setup.need.module` names the tried; tests a1, a2; ic2's f2 reworded | done; the sidecar waits on `make voice` (act 4) |
| 3 R2: `status_read.not_read(parts)`; `_not_read` says a part once; tests a3, a4; su6 test_d, test_e, su2-join's labels and e2e.piped.txt by ruling | done |
| 4 NICE n281; `make voice`; the version; doclint, recordlint, hygiene; `make check` through the gate queue | open |

## Next act

Act 4: NICE n281 (and the bound), `make voice` through the gate, the version, recordlint, hygiene, then `make check` through the gate.

## Handover

- choice: `PYTHONS` is respeak's whole list, its two bare names included, so the two readers agree. Consumer: review.
- choice: an interpreter met twice (one real path) is asked once; `{tried}` names the words of PYTHONS, not the paths. Consumer: review.

- decide, owner: coordinator. Commit 97ac03d's `tests/test_sn1_need_notread.py` names the sibling tool three times (a docstring, `plan.build`'s argument, a test name), gone from the tree since; `--commits main..HEAD` counts it until an allow row `tests/test_sn1_need_notread.py: sibling` stands. Consumer: the landing.

## Exit

In flight.
