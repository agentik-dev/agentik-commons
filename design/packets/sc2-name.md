# Packet sc2-name: the name on the screen, and the command a line prints

| item | value |
|---|---|
| from | agentik-hq's brief sc2-name of 2026-11-13, R1 to R6; hq design/23 §3 and §14 (row sc2-name, §9); level S2 |
| pin | agentik-commons main b62ddad (`Merge sm1-setup-ask`, suite 0.6.1); worktree `.claude/worktrees/sc2-name`, branch `sc2-name`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync into another repo; no bare `make`; no relay verb or binary; no `claude` process; made-up names in fixtures; the door (`bin/agentik`) is sc13's |
| may touch | `plugins/suite/lib/agentik_suite/{prog,cli,apply,config,doctor,install,status,term}.py`; `plugins/suite/lib/agentik_suite/messages.md`; `design/voice/checked.sha256`; `setup`; `scripts/plugin-launcher`; `plugins/suite/bin/agentik-suite`; `tests/test_sc2_name.py` and the tests that pin a printed command (`tests/test_{suite_word,sm1_setup_ask,su1_status_check,ak3d_doctor,ak2b_reach}.py`); this packet; `history/sittings/2026-11-13-13.md`; R6's `plugins/suite/.claude-plugin/plugin.json` |
| verify | `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 5 below; `python3 -m unittest tests.test_sc2_name` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

2026-11-12: "Make it a high quality modern CLI tool that is dynamic and has high quality concise human friendly feedback (using respeak to help with the voice). Make plugin configuration discoverable and drill down." From his first `./setup`, 2026-11-13: the closing hint printed `agentik-suite doctor`, where the door's name is `agentik doctor`; sm1 mended that one line.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (stdlib at Python 3.9, the launcher's interpreter order), hq entry 37 (made-up names).

- R1, one function: `prog.start` (on the command, `cmd.say(*words)`) gives the words that start a printed command; every `next:` hint, error remedy, usage line and doctor `run:` line calls it. The catalogue names a command by its verb's slot (`{setup}`, `{doctor}`, `{config}`, `{status}`, `{help}`, `{describe}`, `{install}`, and `{prog}` for a flag with no verb); `{tool}` is the name alone, in a title. `tests/test_sc2_name.py` fails on a message with `{tool}` before a verb or a flag, and on a source line that writes the tool's name before a verb with `%` or `+`.
- R2, the three answers: `agentik` where the first `agentik` on PATH is a door at 0.2.0 or newer and the tool is on PATH; the door's path, `~` for HOME, where `~/.local/bin/agentik` is such a door and that folder is off PATH; else the word typed (R3).
- R3, the word typed: `setup` and the launcher export `AGENTIK_ARGV0`, the word they were started with; the launcher sets it only where it is unset, so setup's word passes through it. The suite takes it out of its environment at start, so nothing it spawns inherits it. A setup line under `./setup` reads `./setup ...`; any other verb, and any word that no longer names the file from the working folder, reads the launcher's absolute path, `~` for HOME.
- R4, the title's name: `agentik` in R2's first two cases, the tool's name in the third; the version is the suite's.
- R5, `--json`: every command in it is the screen's with the full path for `~`.
- R6, the version: as the coordinator names it, alone in the last commit before the charter's close.

## 3. Interfaces

`AGENTIK_ARGV0`, read once by `cli.Command` and popped. `prog.form(env, lib, tool) -> ("door"|"placed"|"typed", path)`, `prog.start(env, lib, tool, typed, cwd, words, full)`, `prog.first_door(env)` (doctor's, moved). The plan's own `would run:` lines name a file to run, never the name, and stay as they are.

## 4. Acceptance

Measured at b62ddad by a paste proof (scratch, not in the tree): a temp HOME, PATH a folder holding a stub `claude` then `/usr/bin:/bin`; each printed command pasted into `sh -c` from the clone's root.

| # | line | at the pin |
|---|---|---|
| 1 | empty HOME: `./setup --dry-run`, `./setup </dev/null`, the launcher's path with `doctor`, bare, `config`, a bad word: no pasted command exits 127 | 6 of 6 exit 127 (each `agentik-suite ...`) |
| 2 | after the suite's `install-cli` in that HOME, `~/.local/bin` off PATH: each command starts `~/.local/bin/agentik` and runs | 5 of 5 exit 127 |
| 3 | `~/.local/bin` on PATH: each starts `agentik`; no title or command through the door reads `agentik-suite` | each `agentik-suite ...`, exit 0; titles and hints read `agentik-suite` |
| 4 | no door on PATH: each title reads `agentik-suite` | holds |
| 5 | `scripts/plugin-launcher` and `plugins/suite/bin/agentik-suite` byte-identical; `make check` green through the gate queue | identical |

## 5. Not built

The door (sc13), the help screens' rewrite (sc5), any screen's layout or words beyond the name; the launcher `install-cli` writes; a sync into the tool repos.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real HOME's files. The report: head sha, gate id and exit, acceptance 1 to 5 at the pin and now.
