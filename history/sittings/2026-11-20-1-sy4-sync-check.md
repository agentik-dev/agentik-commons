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
| T the failing tests, acceptance 1 to 6: `CheckTest`, six tests, red at the pin (exit 2, usage); the pin's 16 pass | done |
| A R1 to R4: `table` read by both paths, the check, the exits; `tests.test_sync` 22 OK; the write path's stdout, files, modes and bytes equal the pin's on four shapes (plain, lib, lib with conf, plugin with no lib), twice each | done |
| B R5: the header comment; GUIDE's sync sentence, which is in §6 at the pin, not §5 as the brief has it; voice and hygiene clean | done |
| V acceptance 8 by hand: session exit 1, `behind scripts/hygiene` among nine lines, its `git status` unchanged; relay exit 1 (`behind scripts/hygiene`); decisions exit 1 (`behind plugin/lib/agentik_term/term.py`). `make check` through the gate: 20261120-092239-2807 exit 0 at 2f934f4, 1313 tests OK, 845 s | done |

## Next act

None: R1 to R6 built; the review and the landing are the coordinator's.

## Handover

- choice: `--check` is read only as the first word; `<repo> --check` is two words, usage as at the pin. Consumer: review.
- choice: mode is compared as the exact permission bits (`find -perm 755`), as the write path's `chmod` sets them; a checkout made under umask 002 (775) reads `behind`. Consumer: review, hq suite status.
- choice: a symlink at a destination is `behind`, since the write path replaces it with a file. Consumer: review.

## Exit

R1 to R6 built, gate 20261120-092239-2807 exit 0 at 2f934f4; this charter-only commit follows the checked head.

