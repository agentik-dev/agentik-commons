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
| 3 R2: `not_read` from every part's state; `_not_read` says a part once; tests a3, a4 | open |
| 4 NICE n281; `make voice`; the version; doclint, recordlint, hygiene; `make check` through the gate queue | open |

## Next act

Act 3: R2, `status_read.not_read(parts)` and `_not_read`'s once rule; su6 test_d, test_e and e2e.piped.txt by ruling.

## Handover

- choice: `PYTHONS` is respeak's whole list, its two bare names included, so the two readers agree. Consumer: review.

- choice: an interpreter met twice (one real path) is asked once; `{tried}` names the words of PYTHONS, not the paths. Consumer: review.

## Exit

In flight.
