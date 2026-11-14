# Packet fh13-relay-plan: setup says which command it cannot place and names the tool's page

| item | value |
|---|---|
| from | agentik-hq's brief fh13-relay-plan, R1 to R8, and the coordinator's start line of 2026-11-14; level S3 |
| pin | main at 82d634b (suite 0.7.5: fk2-plan, sm2-setup-next and sc3-table landed); worktree `.claude/worktrees/fh13-relay-plan`, branch `fh13-relay-plan`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary, a stub file named `agentik-relay` in a temp HOME at most; no `claude` process, no agent; made-up names (`murmur`, `plain`, `example.com`); no version (the start line: R9 waits on a later word) |
| may touch | `plugins/suite/lib/fallback.json`; `plugins/suite/lib/agentik_suite/tools.py`, `plan.py`, `apply.py`, `cli.py`, `messages.md` (`## Setup`, `## Errors`); `tests/fk_homes.py`, `tests/test_fh13_relay_plan.py` (new); `NICE_TO_HAVE.md`; `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-14-8.md` |
| verify | `make voice`, then `make check`, each once, last, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_fh13_relay_plan` OK |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The finding, measured again at 82d634b

Temp homes from `tests/fk_homes.py` with T `relay`, PATH `~/.local/bin:/usr/bin:/bin` and a folder with a stub `claude`, the suite run from this worktree. An empty home: step 4 `not placed; step 3 installs the plugin first`, step 7 `step 4 places the launcher first`; `relay doctor` `relay is not installed`, exit 3. `relay@agentik` installed, no `bin/`: steps 4 and 7 `ok`, `the plugin ships no command`; `relay doctor` `relay is a plugin with no command`, then `next: ... config relay` (sc4 split the remedy off since the brief's 0.6.2 screen), exit 3. That home with an executable stub at `~/.local/bin/agentik-relay`: steps 4 and 7 as before; `relay doctor` now reads `relay is a tool, not a verb`, exit 2, since the stub is on PATH. Steps 3, 4 and 7 otherwise read as the brief's 0.6.2 screens.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. T is a tool's name; W `~/.local/bin/agentik-T`; `runs` the finder's key in the plan's row for T.

- R1. A row of `fallback.json` may hold `page`, a string that starts `https://`: this tool installs its own command, and this page has the line. The relay's row gains `"page": "https://github.com/agentik-dev/agentik-relay#install"`; no other row gains one. A `page` of another type is read as absent.
- R2. Step 4 for a T with a `page`, whatever step 3 reads, where `runs` is null: `todo`, no command, a line kind `page` whose text is the page: `setup.launcher.page`, then `setup.page`.
- R3. Step 4 for a T with a `page` where `runs` names a file: `ok`, `setup.launcher.theirs`, the path from `~`. No `install-cli` for such a tool, nothing written at W.
- R4. Step 7 for a T with a `page`: `runs` names a file, the pin's doctor row with that file and ` doctor`; `runs` null, `todo` with no command, `setup.doctor.page`.
- R5. A T with no `page` reads as at the pin, byte for byte.
- R6. The page is never run: `apply.runnable` takes `run` lines alone; a `page` row is nothing to do for `apply.planned` and is never counted in the question; nothing opens or fetches the address.
- R7. Where a `page` row is left and no step holds a command setup would run, the dry run's last line and an applied run's report's is `hint.setup.page`, `{names}` the tools in the plan's order joined by `, `. While a command is left to run, the pin's close. It goes before the PATH line's close.
- R8. `cli.Command._not_a_verb`, for a plugin's name with a `page` and no file that runs: `err.verb.page`, exit 3, the remedy as at the pin. A name with no `page` keeps `err.verb.plugin`.
- Not built: R9, the version (the start line); `sources.py`; step 3's rows; the doctor's and config's screens; the door's own line; running the file where one runs (ak9b).

## 3. Acceptance

T is `murmur` with the row `{"lines": ["agentik murmur doctor"], "user_file": null, "needs": [], "status": [], "page": "https://example.com/murmur#install"}` in a temp copy of the suite's plugin; `plain` has no `page`. Each plan is read through `plan.build` and `setup --dry-run T`; the terminal's PATH is `~/.local/bin:/usr/bin:/bin` and a stub `claude`'s folder.

| # | line | pin |
|---|---|---|
| 1 | an empty home: step 4 `setup.launcher.page` with the page under it; step 7 `setup.doctor.page`; no line holds `places the launcher` | `setup.launcher.wait`, `setup.doctor.wait` |
| 2 | `murmur@agentik` installed, no `bin/`, no `agentik-murmur` anywhere: steps 4 and 7 as line 1, neither `ok`; the page once | both `ok`, `the plugin ships no command` |
| 3 | line 2's home with an executable stub at W: step 4 `ok`, `setup.launcher.theirs` with `~/.local/bin/agentik-murmur`; step 7 names W with ` doctor`; no `install-cli` line for T | both `ok`, `the plugin ships no command` |
| 4 | line 2's home with steps 2, 3, 5 and 6 otherwise ok: the dry run ends with `hint.setup.page` naming T; with step 5's command left, the pin's close | `hint.setup.done` |
| 5 | `setup --yes murmur` in line 2's home, the stub `claude`: no process for T's row, the report's last line `hint.setup.page`, no file at W | not measured |
| 6 | `agentik-suite murmur` in line 2's home: `err.verb.page` with the page, exit 3; `--json` `error.code` `not_installed` | `err.verb.plugin`, exit 3 |
| 7 | `plain` in each home of lines 1 to 3 reads as at the pin; the pin's own tests pass unchanged | itself |
| 8 | a `page` that is a number or a list is read as absent: the plan is line 7's | no key |
| 9 | each `next:` and `yours to run later:` line of lines 1 to 4, run by `sh -c` in that home with stdin closed, exits other than 127; `hint.setup.page` is no command and is left out | not measured |
| 10 | at 60 columns on a pty, the page stands whole on its own line | not measured |
| 11 | `make voice` green with the sidecar committed; the suite's tests under `/usr/bin/python3`; `make check` green | green |

## 4. Review 1's ruling, the fix round

The coordinator's ruling on review 1 (adversary, slice `82d634b..12677ea`), built at the branch tip `aad26fc`, no version, main not merged:

- F1. `hint.setup.page` is printed only when step 4's row and its `setup.page` line stand above it on the same screen: an applied run's report (`show(..., lines=False)`) keeps the `page` line under step 4, and a run with nothing to do prints step 4's row and its page before the close, for `setup T` with stdin closed and `setup --yes T`, the suite placed or not. The page is still never run, opened or fetched (R6).
- F2, R2 to R4 amended. A file that runs is the file `runs` names or, where `runs` is null, W when W is a file the finder's own test (`sources._executable`) calls executable. Then step 4 is `setup.launcher.theirs` with W from `~`, ok; step 7 the pin's doctor row with W's path and ` doctor`; no page row is left, so step 6's add line carries the close as at the pin. No `install-cli` for T, nothing written at W. A dangling link, a file that is not executable, or a folder at W stays R2.
- R1 narrowed. A `page` holding whitespace or a character that is not printable (a control or format character) reads as absent (line 8).

| # | line | at 12677ea |
|---|---|---|
| 12 | settled `hL`, `setup T` with stdin closed and `setup --yes T`: `Setup has nothing to do`, then step 4's row with the page under it, then `hint.setup.page`; nothing ran | red: no page on the screen |
| 13 | `hL`, `setup --yes T`: the report's step 4 row has the page under it; the last line `hint.setup.page` | red: no page under step 4 |
| 14 | settled `hM`, PATH without `~/.local/bin`: step 4 ok `setup.launcher.theirs` at W, step 7 `W doctor`, no page; the dry run's close `hint.setup.path`; `--yes` prints the add line, closes as the pin's report (`hint.setup.doctor`), leaves W as it was and runs nothing of T | red: `setup.launcher.page` |
| 15 | a dangling link, a plain file or a folder at W, on PATH or off: steps 4 and 7 the page's | green |
| 16 | a `page` with a space, a newline, a tab, ESC, NUL, BEL, U+202E or U+00A0 reads as absent | red: read as a page |
