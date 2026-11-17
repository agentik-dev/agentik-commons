# Packet ic1-close: the last line of `setup` and of `doctor` runs as printed and names the one act left

| item | value |
|---|---|
| from | agentik-hq's brief ic1-close of 2026-11-16, R1 to R7; the first-install review's findings 3, 4, 9 and 10; hq design 23 section 8 (the voice rules); level S3 |
| pin | agentik-commons main 93f0202 (suite 0.7.24); worktree `.claude/worktrees/ic1-close`, branch `ic1-close`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME with a stub `claude`; made-up names in fixtures |
| may touch | `plugins/suite/lib/agentik_suite/apply.py` (`show`, `_before`, `report`), `doctor.py` (`door`, `close_command`, `_under`, `screen`), `term.py` (`error`), `cli.py` (the dry run's rows, now `apply.show`), `plan.py` (one helper: is `~/.local/bin` on PATH), `messages.md` (`hint.setup.doctor`, one new `doctor.door.off`), `design/voice/checked.sha256` (by `make voice`), `tests/test_ic1_close.py` (new), the tests that pin a line changed here, `NICE_TO_HAVE.md` (five rows), `history/NICE-overflow.md` (the oldest S4 rows, moved by recordlint's size bound), `plugins/suite/lib/agentik_suite/update.py` (the blocked close, review 1), `history/sittings/2026-11-16-1-ic1-close.md`, `plugins/suite/.claude-plugin/plugin.json` (the version, alone, last), this packet |
| verify | `make voice`, then `make check` once, last, through the gate queue |
| acceptance | 1 to 4 below |

## 1. The owner's words

"Use up to 2 Fable agents to review our upgrade/install so far. Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

## 2. Rulings

- R1, `hint.setup.doctor` is a command and nothing after it (`next: {doctor}`), after an applied run and after "nothing to do". A test runs the printed line as printed in a temp HOME and it exits 0 or 1 as doctor rules, never 2.
- R2, where the door stands in `~/.local/bin` and only PATH lacks that folder: doctor's door row, doctor's close and setup's close each name the PATH line, the one `setup --dry-run` closes on today (`hint.setup.path`). Setup and doctor never name each other in that state.
- R3, plain `setup` with `claude` missing prints the `get it:` address as the dry run does, and its close names the command he ran, not a dry run. A Python under 3.9 is said to be too old, with its version; never "install python3" where one is installed.
- R4, stdout is flushed before the question and before a refusal: through a pipe the plan prints above the FAIL line; `next:` prints after "The plan, read again after the run:" and its rows. Tests with a pipe. Its `| tee` clause is withdrawn by review 1's ruling (see section 2a).
- R5, every message changed holds section 8 and the width test; `make voice` through the gate. No other line of setup's screens changes.
- R6, two lines join `NICE_TO_HAVE.md`, S4: `issue.strike.none` says Struck and unchanged at once; `usage.issue` drops the `[TOOL]` that `issue new` takes.
- R7, suite 0.7.25, alone in the last commit.

## 2a. The fix of review 1 (the coordinator's ruling, 2026-11-16)

- F2: for a Python installed and under the minimum, `err.setup.blocked` (setup's `--json` refusal) and `hint.setup.blocked` (update's close) have an older-than form, `err.setup.blocked.old` and `hint.setup.blocked.old`, that gives the version found and the minimum and never says "install". The `--json` remedy in that state is null, never a dry run. A missing `claude` or `git` reads as before.
- With F2: plain setup's close in that state is the reason line `hint.setup.blocked.old` and no `next:`, since no command of ours mends it (GUIDE section 11.5: a remedy is a command or null). It never sends him into the same refusal.
- The PATH close, where the door stands in `~/.local/bin` and only PATH lacks it: setup's close, the dry run's, doctor's close and doctor's door row end on the command `export PATH="$HOME/.local/bin:$PATH"`, the plan's step 6 line, so a prefix's folder would be named there. The closes print the reason `setup.path.why` above `next: {command}` (`hint.setup.path`); the door row's line under it is `fix:` and the command; `doctor --json`'s remedy is the same command. The prose `next:` is gone.
- F1 is not built: R4's `tee` clause is withdrawn. The case, and the review's leads (`get it:` in update's and remove's plans, a foreign file at the door), are NICE rows.

## 3. Interfaces

- "The door stands and only PATH lacks its folder": setup reads it from its plan, step 5's `door` row ok and step 6's `path` row todo; doctor reads it as no `agentik` on PATH, a regular executable file at `~/.local/bin/agentik`, and `~/.local/bin` not among PATH's folders (`plan.bin_on_path`, the one test step 6 uses).
- Doctor's door row in that state: warn, detail `doctor.door.off`, remedy the profile line (`export PATH="$HOME/.local/bin:$PATH"`, so `--json` carries it); on the screen no `fix:` line under it, since step 6's row holds that line marked add. `close_command` returns `doctor.PATH`, which the screen prints as `hint.setup.path`.
- Setup's close, in order: a failure's refusal; the page close (fh13 R7); `hint.setup.path` in R2's state; else `hint.setup.doctor`.
- Plain setup, step 1 blocked: the plan with the `get it:` line under a missing `claude` (`apply.show`, which the dry run now calls too), then `hint.setup.next` naming `setup` and the names given, as the dry run's close does. `--json` is unchanged.

## 4. Acceptance

Each in a temp HOME, PATH a folder with a stub `claude` then `/usr/bin:/bin`, the stub installing a made-up plugin set as the plan tests' stub does; the suite starts as `./setup` from the worktree.

| # | line | at the pin |
|---|---|---|
| 1 | after `./setup --yes`, and again after "nothing to do", the closing `next:` pasted into `sh -c` as printed exits 0 or 1 (`tests/test_ic1_close.py`) | `next: …/agentik-suite doctor checks each plugin.`; pasted: `FAIL  doctor takes no name; checks is one more`, exit 2, both times |
| 2 | with `~/.local/bin` off PATH and the door placed there: setup's close and doctor's close are `hint.setup.path`; doctor's door row names it; neither names the other | setup: `next: ~/.local/bin/agentik doctor checks each plugin.`; doctor: `warn door no agentik command on PATH`, `next: ~/.local/bin/agentik setup` |
| 3 | `./setup 2>&1 \| cat` prints the plan, then the refusal; the `\| tee` clause is withdrawn, since a flush cannot order a pipe that tee copies against a terminal, and the case is a NICE row | the FAIL line first, the plan under it |
| 3a | plain `./setup` with no `claude`: one `get it:` line under its row, close `next: ./setup`; a Python under 3.9: no `install python3` | no `get it:` line; `next: install claude, then ./setup --dry-run again.` |
| 4 | `make voice` exits 0; `make check` green through the gate; `scripts/hygiene --require-private --commits main..HEAD` exits 0 | green |
| 5 | a Python under the floor (in process, `FLOOR` raised): setup `--json` refuses with the version and the minimum, no "install", remedy null; update's close and plain setup's close are the older-than line and no `next:` (`-k test_f2`) | at 4e7b50e: "Install it", remedy `setup --dry-run`; update `next: install python3, then ...`; setup `next: agentik setup` |
| 6 | off PATH with the door placed: setup's, the dry run's and doctor's closes are `setup.path.why` then `next: export PATH="$HOME/.local/bin:$PATH"`, which pasted exits 0; doctor's door row has that `fix:` line (`-k test_path`) | at 4e7b50e: `next: add the line marked add above to your shell profile, then open a new terminal.`, pasted exit 127 |

## 5. Not built

At review 1's fix: the dry run's close and doctor's close with an old Python still name setup; `err.update.blocked` (update's `--json`) still says install. Before it:

`update`'s own close on a blocked step (`hint.setup.blocked`, which it still prints); setup's `--json` refusal for a blocked step (`err.setup.blocked`, its remedy a dry run); the first screen's close in R2's state, which names doctor, and doctor names the PATH line, so no loop.
