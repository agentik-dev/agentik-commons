# Packet hn1-help-next: the help's next line asks setup's own question; a described read keeps its wall; `sync --check` compares the executable bit alone

| item | value |
|---|---|
| from | agentik-hq's brief hn1-help-next of 2026-11-20, R1 to R5, on the row's designs D1 to D3 (an advisor's runners-up 1 and 4, and sy4-sync-check's review 1, lead L1); level S3 |
| pin | agentik-commons main b4b4cc8 (suite 0.7.37); worktree `.claude/worktrees/hn1-help-next`, branch `hn1-help-next`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no tool synced or written; no test reads the live home or state; made-up names in fixtures |
| may touch | `plugins/suite/lib/agentik_suite/cli.py`, `plugins/suite/lib/agentik_suite/status_read.py`, `scripts/sync`, `tests/test_hn1_help_next.py`, `GUIDE.md` (the sentences R2 and R3 make false), `design/packets/hn1-help-next.md`, `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | `python3 -m unittest tests.test_hn1_help_next tests.test_sync tests.test_su2_read` and `-k test_r2_the_closing_hint_by_state` directly; `make check` once, last, through the gate queue; `scripts/hygiene --require-private` on the tree and on `--commits main..HEAD` |
| acceptance | 1 to 10 below |

## 1. The finding

The owner's words, 2026-11-20: "continue with the charter". The charter orders this row second: one commons row carrying the sync check's mode lead and the advisor's two runners-up. At the pin `agentik --help` closes on the setup line where any step up to 5 is not `ok`, while setup's own dry run on the same plan says it has done what this version can (a `warn` row for a missing optional package is enough). A status read learned from a tool's `describe` runs under 1 s whatever `wall_s` it names, though GUIDE §11.3 lets it name up to 10. `sync --check` compares a copy's exact permission bits, while git keeps the executable bit alone, so a clone under umask 002 reads every copy `behind`.

## 2. Rulings

- R1, one question (D1): `_close_help` and the setup dry run's close ask `_closing` over the same steps; the help says `hint.help` (the setup line) where it returns anything but `hint.setup.done` or `hint.setup.rest`, else `hint.help.done`. Steps, names and the setup line as at the pin; `-q` says nothing; `_closing`'s results unchanged.
- R2, a described read keeps its wall (D2): in `release()`, a status read's wall is its `wall_s` where that is a number, never a bool, above 0 and at most 10, else `WALL`. The fallback table's reads as at the pin. The job's wall and the source's `wall_s` (a `timed out` read's ms, the JSON) are that value.
- R3, the mode as git keeps it (D3): in `--check`, a copy of commons' bytes is `behind` on its mode only where its owner's executable bit differs from the table mode's; `place` sets the table's mode as at the pin; the header comment says so.
- R4, what stands: no new verb, flag, key or message id; `hint.*` texts unchanged; the fallback table stays. GUIDE changes only where a sentence is now false: §6's sync sentence ("in bytes or mode"), §11.1's status wall and §11.3's `reads` row ("once its fallback table is gone").
- R5, the NICE: no row of `NICE_TO_HAVE.md` names the three at the pin (grep of `wall_s`, `perm`, `umask`, `hint.help`, `_close_help`), so none closes and none is added.

## 3. Interfaces

- `cli.Command._close_help` reads `self._closing(steps, setup)`; `HELP_DONE = ("hint.setup.done", "hint.setup.rest")` the closes on which the help says the doctor line.
- `status_read._described_wall(value)`: `value` where a number, not a bool, `0 < value <= 10`, else `WALL`.
- `scripts/sync --check`: the owner's executable bit read with `find <f> -prune -perm -0100`; the table mode's from its first digit.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `-k test_a1_a_warn_step_and_nothing_to_run`: a step up to 5 `warn`, no run line, the help's close `hint.help.done` | `hint.help` |
| 2 | `-k test_a2_the_help_agrees_with_setup`: each state of `test_r2_the_closing_hint_by_state`, the help's close by R1's rule | agree in both |
| 3 | `-k test_a3_a_blocked_step_one`: the help says the setup line | the setup line |
| 4 | `-k test_a4_a_described_wall_is_kept`: `wall_s` 6, a 1.5 s read: drawn, `wall_s` 6 | `timed out`, 1000 ms |
| 5 | `-k test_a5_a_wall_out_of_range_is_one_second`: 0, -1, 11, `true`, `"6"`, absent: 1 s | 1 s |
| 6 | `python3 -m unittest tests.test_su2_read`: the su2 screens unchanged | 14 OK |
| 7 | `-k test_a7_the_group_bit_is_not_compared`: `chmod 775` executable, `664` plain: exit 0, the one line | `behind` each, exit 1 |
| 8 | `-k test_a8_the_executable_bit_is_compared`: `644` executable, `755` plain: `behind` each, exit 1 | `behind` each, exit 1 |
| 9 | not a test: the last line of the worktree's `--help` and of the setup dry run it names, this Mac read only | `next: agentik setup session decisions agents observer relay respeak`; dry run `next: setup has done what this version can.` |
| 10 | `make check` through the gate queue | green at b4b4cc8 |
