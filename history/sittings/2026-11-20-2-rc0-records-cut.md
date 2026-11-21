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
| A R1 to R6: the script | open |
| B R7: the header, GUIDE §12, a NICE row | open |
| V acceptance 8 and 9 | open |

## Next act

A: `scripts/records-cut`, R1 to R6.

## Handover

None yet.

## Exit

Open.
