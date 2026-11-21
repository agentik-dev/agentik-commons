# Sitting 2026-11-20-2-rc0-records-cut: row rc0-records-cut, `scripts/records-cut` (builder)

| item | value |
|---|---|
| goal | packet `design/packets/rc0-records-cut.md`: R1 to R7, acceptance 1 to 9 |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | main b4b4cc8; nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; `--go` only in a test's temp folders |
| verify | `python3 -m unittest tests.test_records_cut` directly; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| P the packet | done |
| T the failing tests, acceptance 1 to 7: ten tests in `tests/test_records_cut.py`, red at the pin (no script) | done |
| A R1 to R6: `scripts/records-cut`; `tests.test_records_cut` 10 OK | done |
| B R7: the script's header; GUIDE §12's new paragraph `The cut.`; NICE n261 (no `--undo`); recordlint and hygiene clean | done |
| V acceptance 9: the dry run against one sibling tool checkout, exit 2: 96 records, refused on 6 branches with record commits and a scanner behind commons'; its `git status` unchanged. Acceptance 8: gate 20261120-172023-2860 exit 2 at 82de088 (the known flake `test_up2_suite_origin` test_12, OK alone; NICE n262); gate 20261120-181118-2867 exit 0 at 91e11b3, 1323 tests OK; `scripts/hygiene --require-private --commits main..HEAD` exit 0 | done |

## Next act

None: R1 to R7 built; the review, the phase 2 and the landing are the coordinator's.

## Handover

- choice: a seventh refusal past R4: the clone's own `scripts/hygiene` absent at HEAD, or holding other record names than the script's (loaded from its path), since the move's proof runs it after the commit. Consumer: review.
- choice: a `.hygiene-allow` line the scanner refuses as a near declaration (`records: out # why`) is refused with the `records` row, since the proof's scan would exit 2 after the commit. Consumer: review.
- choice: refusals and failed steps go to stderr, the report to stdout; the dry run prints its plan even when it refuses. Consumer: review.
- choice: a failed commit leaves the staged removal and the copies; the line names `git reset -q --hard HEAD` (the tree was clean) and the copies to remove, as R5 says nothing is reverted by itself. Consumer: review.

## Exit

R1 to R7 built, gate 20261120-181118-2867 exit 0 at 91e11b3; this charter-only commit follows the checked head.
