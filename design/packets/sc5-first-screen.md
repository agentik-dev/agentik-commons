# Packet sc5-first-screen: bare `agentik` is a first screen of ten lines that names the tools, and `help` is the full list

| item | value |
|---|---|
| from | agentik-hq's brief sc5-first-screen of 2026-11-12, R1 to R7, acceptance 1 to 10, and the coordinator's start line of 2026-11-14 (the pin, the `status` row, the door, the widths, and R8, doctor's close, from sc4-errors' phase 2); level S3 |
| pin | main at 2fd5a80 (suite 0.7.6, door 0.3.0); worktree `.claude/worktrees/sc5-first-screen`, branch `sc5-first-screen`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no test reads the live home; made-up names; no version (other rows land first) |
| may touch | `plugins/suite/lib/agentik_suite/cli.py` (`_dispatch`, `do_help`, `help_verb` and what they call); `messages.md`'s `## Help` and the one `## Doctor` id R8 needs; `doctor.py`'s `close_command` alone; `tests/test_sc5_first_screen.py`; the older tests that hold a line a ruling changes; `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-14-9.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `tests/test_door.py` green as it stands |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The owner's words

2026-11-12: "Make it a high quality modern CLI tool that is dynamic and has high quality concise human friendly feedback". And: "Make plugin configuration discoverable and drill down."

## 2. What a person meets at the pin

Measured at 2fd5a80 in a temp HOME, `env -i`. "Empty": a stub `claude`, then `/usr/bin:/bin`, the suite by its launcher's path. "Finished": steps 1 to 5 ok, the door at `~/.local/bin` on PATH, three stub tools (`murmur` answers `describe --json`, `paint` and `quill` print nothing), a plugin `sketch` installed with no command.

1. `agentik`, `agentik help` and `agentik-suite` are the same bytes. Finished: 26 lines and the hint in a pipe; on a pty (`script`, `NO_COLOR=1`) 38 lines at 80 columns and 43 at 60, the longest 101 columns (a tool's path). Empty: 23 lines and the hint, the longest 145 (the launcher's path in the usage line). The brief's 0.6.2 count differs (27 for the empty home); the shape is the same.
2. No line says that `agentik <tool>` runs a tool; the tools show as files, four rows of `ok  agentik-<name>  <path>`, the suite's among them. `sketch` shows nowhere.
3. `help config`: usage, sentence, blank, `flags`, six rows, and `next: agentik help lists every verb and the agentik commands on PATH.`; no example. 10 lines and the hint; 82 columns at the longest.
4. A tool's failing check with the remedy `agentik-murmur reset --yes` closes doctor on `next: agentik-murmur reset --yes`, the row holding no `fix:` line.

## 3. Rulings

Cited: hq design/23 §3 (`cmd.say`) and §8 (the voice); hq entry 37 (made-up names).

- R1, two screens. With no word and no `--help`, the first screen. `help`, `-h`, `--help` with no verb, the full list. Neither is a verb; each exits 0.
- R2, the first screen, at most 10 lines with the hint: the title (`{tool}` slot, the suite's version, `one command for the agentik tools`), a blank, rows `setup`, `doctor`, `config`, `status`, `help`, `<tool>`. The `<tool>` row names each listed tool with a command, by name (`run a tool: murmur, paint, quill`), else `run a tool; none is installed yet`. No path, no mark, no process: the names come from `tools.listed`. `status`'s row is `the watchers, sessions, gate, backlog and runs on one screen` (su2's join has landed).
- R3, the close of both screens is sm2's, as at the pin.
- R4, the full list: the title; `usage: <say()> <verb> [<name>...] [flags]` and a second line under its command, `<tool> [<its words>...]`; `verbs` with the five rows (help's: `this list; help <verb> for one verb, help <tool> for a tool's own`) and `more` naming every other verb; `tools`, a row a listed tool but the suite: name, version and summary from its `describe --json` through `config.Reader.survey` with no config read (its cache, its wall), the name alone for no answer, `a plugin with no command` for a plugin with none; `flags    --json  -q/--quiet  --no-color  -h/--help`. No path.
- R5, `help <verb>`: the `usage.*` line, the `verb.*` sentence, a blank, the examples where the table has them, a blank, the `flags` title and the verb's own flags with their `flag.*` words, then `also` with `--json  -q/--quiet  --no-color`. No hint: `hint.verb` leaves. An example's command comes from `cmd.say`.

| verb | example: gloss |
|---|---|
| setup | `setup`: the default set, after one question; `setup --dry-run`: the plan; nothing is written; `setup <plugin>...`: those plugins and no others |
| config | `config`: every tool, and how many keys changed; `config suite`: one tool's keys; `config suite.kind`: one key, where it is set and how to change it |
| help | `help`: every verb, tool and flag; `help config`: one verb, with examples; `help <tool>`: that tool's own help |

- R6, `--json` with no word and with `help`: the pin's `agentik.help/1` and one more key, `tools`: `[{name, version, summary, command}]`, `command` true or false, the two before it null where R4 prints none. Every other key keeps the pin's bytes.
- R7, the catalogue: new ids for the rows, the usage's second line, `more`, `tools`, the no-command line, the nine glosses and `also`; `help.path`, `help.path.none` and `hint.verb` leave. No `verb.*`, `flag.*` or `usage.*` changes a byte. A new message: at most 76 characters before its values, the present tense, `key`, no path, no code.
- R8, doctor's close (the coordinator's, 2026-11-14, reversible): a tool's remedy goes behind the close's `next:` only when it holds no word of `cli.SKIPS` and not the word `remove`. One that fails stands on its check's line as the tool wrote it, and the close names `agentik <tool> doctor`, the tool's own doctor through the door, with no door the tool's file and `doctor` (`doctor.tool_doctor`). A write such as `install-cli` or `setup` stays the close. Amended by review 1 F1 (the coordinator, 2026-11-14): the first build's `agentik doctor <tool>` exits 2, since doctor takes no name.

- R5 amended by review 1 F2 (the coordinator, 2026-11-14): an example's command is never wrapped. On a terminal where the command and its words do not fit side by side (the widest command past a third of the width, or a row past the width), each command stands whole on its own line, two spaces in, and its words on the next, six in, wrapped to the width; where they fit, the rows read as at the pin. The builder's choice: the whole block stacks or none does, so the words of one block keep one column. Off a terminal one row is one line, as every table.

The builder's reading: with no door, the usage's second line names the tool's own command, `agentik-<tool>`, since the suite by its own name runs no tool; `more` holds every verb not in the five rows (`inbox` and `issue` came after the brief); with no tool the full list's `tools` holds one row, `none is installed yet`.

## 4. Acceptance

Each in a temp HOME under `env -i`, the homes of §2.

| # | line | at the pin |
|---|---|---|
| 1 | empty, no word: at most 10 lines with the hint; the last row `none is installed yet`; the hint the pin's | 24 lines |
| 2 | finished, no word, by the launcher and by the door: at most 10 lines; the last row names murmur, paint, quill in order and not sketch; no `/`; the hint the pin's | 27 lines, 4 of paths |
| 3 | no word, both homes, `subprocess.Popen` raising: the screen prints | holds |
| 4 | finished, `help`, `-h`, `--help`: the same bytes, R4's parts in order; murmur's row its version and summary, paint's its name alone, sketch's `a plugin with no command`; no home path | no tool but as a file |
| 5 | line 4's screen holds `usage:` and `tools`; line 2's neither | the same bytes |
| 6 | `help setup`, `help config`, `help help`: three example rows each; each with no `<`, pasted into `sh -c` with stdin closed, exits other than 127; one `also` line; stderr empty | no example; a hint |
| 7 | `help doctor`, `help version`, `help status`: usage, sentence, flags; no example; stderr empty | a hint |
| 8 | `--json` bare and `help`: R6's `tools`; every other key byte-equal to the pin's | no `tools` |
| 9 | no `verb.*`, `flag.*`, `usage.*` changed; no new message past 76 characters before its values | |
| 10 | R8: a tool's failing check with `agentik-murmur reset --yes`, and one with `remove`: `next: agentik murmur doctor` (F1), the remedy on its row byte for byte, and a warn the same; with `agentik-murmur install-cli` the close is that command; in the finished home the close pasted under `sh -c` exits neither 2 nor 127 | red, red, holds; at 6d73e06 the close exits 2 |
| 12 | F2, on a pty: finished, `help config` at 60 shows `agentik config suite.kind` whole on one line, and at 80 the rows as before; empty, `help setup` at 80 and 60 shows the launcher and `setup`, `setup --dry-run`, `setup <plugin>...` each on one line | red, red at 6d73e06; the rows at 80 hold |
| 11 | `tests/test_door.py` as it stands; `make voice` and its sum; the suite under `/usr/bin/python3`; `make check` once, last, through the gate queue | |

## 5. Not built

The refusal for a word near a tool's name (sc4); bare `agentik` through a door older than 0.3.0 (sc13); a row's width (sc3); `--pick` in `help config` (sc14); `doctor <tool>` as a read (fk2b-reads); the version (phase 2).
