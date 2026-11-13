# Packet ak3-setup: `setup` applied: the plan run step by step, its report and its journal

| item | value |
|---|---|
| from | agentik-hq's brief ak3 of 2026-11-13, R1 to R11; hq design/15's row ak3, first half (§7.1, §9); level S3 |
| pin | agentik-commons main d795d4a (suite 0.5.0); worktree `.claude/worktrees/ak3-setup`, branch `ak3-setup`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; every run in a temp HOME with a stub `claude`; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/apply.py`; `plugins/suite/lib/agentik_suite/term.py` (`append` alone); `plugins/suite/lib/agentik_suite/cli.py` (`do_setup` and the package import); `plugins/suite/lib/agentik_suite/messages.md` (R11's ids); `tests/test_ak3_setup.py`; `tests/test_agentik_suite.py` (a6's three setup lines, `STDLIB`); `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-13-9.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_ak3_setup` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"I want to use it today." Three builders work beside this one from the same pin (the suite's `install-cli`, `doctor`, a probe); a join merges the four branches, so this row touches only the files named, and in a shared file only the lines named.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 31 (the settings file may be on the owner's gate list), hq entry 37 (made-up names).

- R1, what stands: the packets ak1a, ak1b, ak2-door and su1: the floor, `term` the one writer, the catalogue and its voice, the streams, the `--json` object, the four exits, no tool's name in the package or its tests. New: `apply.py`, `tests/test_ak3_setup.py`. `setup --dry-run` prints what it prints at the pin.
- R2, read first: `setup [PLUGIN...]` builds the plan (`plan.build`, not edited) and loops: take the first row of steps 2 to 5 that is `todo`, has a `command` and whose `line` is `run`; run it; build the plan again; stop when no such row is left. A command runs once: a row that still names a command already run has failed. Step 7 is never run nor reported; the closing hint names `<tool> doctor`. Step 6 is never applied; its `add` line closes the report while it is todo.
- R3, a command: `shlex.split`, no shell, stdin the null device, both streams captured, its own process group, a wall of 600 s where its first word is `claude` and 120 s otherwise, the group killed past it. A non-zero exit, the wall or a file that cannot start is a failed step: the run stops, exit 1, and the report names the command, its exit and its last line of output. No rollback.
- R4, the step beside this one: after the join step 5's `suite` row carries `<launcher> install-cli`, run as any row. At the pin it has no command, so the tests place a made-up launcher, and one test in process gives `apply` a step 5 row whose command is a stub.
- R5, asking: before the first command, where stdin and stderr are terminals and `--yes` is absent: the plan, then one question; any answer but `y` or `yes` is exit 2, nothing run. Off a terminal without `--yes`: the plan, a line naming `--yes`, exit 2. A step 1 row `blocked`: exit 2, nothing run, the pin's hint.
- R6, the gate: `claude plugin marketplace add` and `install` both write `${CLAUDE_CONFIG_DIR:-~/.claude}/settings.json` (measured). Off a terminal, where a step 2 or 3 row is todo and the user's gate list names that file, even `--yes` is exit 2, nothing run, one line naming the file and saying to run setup from a terminal. The list is `edit-gates` in that folder: a path or glob a line, `#` a comment, a leading `~/` the home. A line names the file when it equals its path or real path, or `fnmatch` matches either. No list, no refusal.
- R7, what was written: `lstat` before and after each command of `~/.claude.json`; `settings.json`, `plugins/known_marketplaces.json`, `plugins/installed_plugins.json` in the config folder; each entry of `~/.local/bin`; each entry of each `~/.local/share/agentik-*`. New or changed is written. After a step 3 command the plugin's `installPath` is listed when new.
- R8, the report, on stdout: the plan after the run, steps 1 to 6, each row with its mark; a `ran:` line per command with its exit; a `wrote:` line per path, as the user would type it. When no command ran: the line `nothing to do`, then step 6's `add` line when todo; nothing written. While a command runs one stderr line names it; `-q` and `--json` show none.
- R9, the journal: `${XDG_STATE_HOME:-~/.local/state}/agentik-suite/setup.jsonl`, one JSON object a line, appended by each run that ran a command: `at` (ISO 8601, UTC), `version`, `plugins`, `ran: [{n, command, exit}]`, `wrote`, `exit`. It is in `wrote`. The append is `term.append(path, text)`, since `WriterTest` refuses a `.write` elsewhere.
- R10, `--json`: `schema` `agentik.setup/1`, `ok`, `dry_run` false, `plugins`, `steps` (after the run, the dry run's keys), `ran`, `wrote` (absolute), `nothing`, `journal` (path or null). A failed step: `ok` false, `error` code `step_failed`, the other keys kept, exit 1.
- R11, shared lines: `cli.py` `do_setup` and the import; `messages.md` `verb.setup`, `usage.setup`, `flag.yes`, `err.setup.plan_only`, new ids at the end of `## Setup`; `test_agentik_suite.py` a6's three setup lines and `fnmatch` in `STDLIB`.

## 3. Acceptance

Each in `Home`, off a terminal unless a pty, `claude` the plan tests' stub that also records its calls, made-up plugins `alpha` and `beta`, a made-up `agentik-suite` launcher placed at this version. At d795d4a (measured): `setup`, `setup --yes` and `setup --yes alpha` print `Setup needs --dry-run: version 0.5.0 only plans, and it wrote nothing.`, exit 2, no call.

| # | line |
|---|---|
| 1 | `setup --yes alpha beta`: exit 0; calls in order: marketplace add, install alpha, install beta; then each install-cli; a `ran:` line for each of the five, a `wrote:` line for each launcher, the door and the journal; the journal one line; the dry run then reads steps 2 to 5 ok |
| 2 | again: `nothing to do`, exit 0, HOME outside the cache unchanged, no new call, the journal still one line |
| 3 | without `--yes`: the plan, a line naming `--yes`, exit 2, no call, HOME unchanged |
| 4 | on a pty it asks once; `n`: exit 2, no call; `y`: as line 1 |
| 5 | the stub exits 1 on `install beta@agentik` with a last line: exit 1; alpha installed; the report names the command, exit 1 and that line; no install-cli for beta; the journal's line `"exit": 1`; mended, a second run exits 0, then line 2 holds |
| 6 | no `claude` on PATH: exit 2, nothing run; a command past a wall shortened in process: a failed step, its group gone |
| 7 | `edit-gates` holding `~/.claude/settings.json`, then `~/.claude/*.json`: `setup --yes` exits 2, names the file, no call; steps 2 and 3 ok and a launcher to place: it runs; on a pty with `y`: it runs |
| 8 | `--json` for lines 1, 2 and 5: one object as R10, the same exits |
| 9 | in process, a step 5 row whose command is a stub: run as any row; one that leaves its row todo: exit 1, run once |
| 10 | `~/.local/bin` off PATH: exit 0, the `add` line closes the report, no file new under HOME outside R7's places and the journal's folder |
| 11 | `make voice`, then `make check`, each once through the gate queue, green |

## 4. Not built

The suite's `install-cli` and step 5's command, `doctor`, the probe (the rows beside this one). Running a tool's doctor. A step list redrawn in place. `remove`, `update`. The README and the version (the join).

## 5. The landing

`plugin.json` stays 0.5.0: the join takes 0.6.0. More than ten messages are new, so the coordinator owes a respeak pass over the joined catalogue, then `make voice` again.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real user's Claude Code files. The report: head sha, gate ids and exits, acceptance 1 to 11 at the pin and now.
