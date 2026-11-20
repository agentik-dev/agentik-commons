# Sitting 2026-11-20-1-sy4-sync-check: row sy4-sync-check, `scripts/sync --check <repo>` (builder)

| item | value |
|---|---|
| goal | packet `design/packets/sy4-sync-check.md`: R1 to R6, acceptance 1 to 9 |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | main 206dfb4 (suite 0.7.37); nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; no tool synced or written |
| verify | `python3 -m unittest tests.test_sync` directly; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| P the packet | done |
| T the failing tests, acceptance 1 to 6 | open |
| A R1 to R4: the table, the check, the exits in `scripts/sync` | open |
| B R5: the header comment and GUIDE's sync paragraph | open |
| V acceptance 8 by hand; `make check` through the gate | open |

## Next act

T: the `CheckTest` class in `tests/test_sync.py`.

## Handover

- choice: `--check` is read only as the first word; `<repo> --check` is two words, usage as at the pin. Consumer: review.

## Exit

