# Packet sc10-doctor-checks: doctor shows each failing check by name, folds what is well, and ends on one command

| item | value |
|---|---|
| from | agentik-hq's brief sc10-doctor-checks of 2026-11-13, R1 to R11 (R4 held); level S2 |
| pin | agentik-commons main 2bf868c (`Merge sc2-name`, suite 0.6.3); worktree `.claude/worktrees/sc10-doctor-checks`, branch `sc10-doctor-checks`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process; made-up names in fixtures; `term.py`, `plan.py`, the tools' doctors and the contract are not this row's |
| may touch | `plugins/suite/lib/agentik_suite/{doctor,cli}.py`; `plugins/suite/lib/agentik_suite/messages.md`; `design/voice/checked.sha256`; `tests/test_sc10_doctor_checks.py`; `tests/test_ak3d_doctor.py` and the tests that pin doctor's lines; this packet; `history/sittings/2026-11-13-24.md` |
| verify | `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_sc10_doctor_checks` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5`; no version (phase 2 names it) |

## 1. The owner's words

After his first setup, 2026-11-13: "it wasn't clear if I was suppose to type run." 2026-11-12: "high quality concise human friendly feedback".

Measured at suite 0.6.2: a tool whose `doctor --json` exits 2 with one `fail` check read as `FAIL doctor` and the tail of a warn; another exiting 0 with a `fail` check read `ok its doctor exits 0`; a third answers an object with no `schema`.

## 2. Rulings

- R1, the read. Each listed tool that has a file is asked `doctor --json`, all at once, under the pin's one deadline. An answer counts when stdout is one object whose `schema` is `agentik.doctor/1` and whose `checks` is a list in the contract's §5 shape, each `status` one of its four words. The tool's exit and its `ok`, `failed` and `warned` are not read. Such an object with `ok` false is one `fail` check, `doctor`, with the error's `message` and `remedy`.
- R2, no such answer: the tool is asked plain `doctor` in a second round under the same deadline and judged by that exit. One check, `doctor`, `ok` or `fail`; its lines are not printed. Slow or unable to start keeps the pin's two warns.
- R3, the verdict: exit 1 when any check is `fail`, else 0. R4 (a check's `scope`) is held: no `scope` key is read.
- R5, the screen. No title. One line a group (mark, name, summary): `{count} checks` when all is well, else the non-zero parts of `{n} failed`, `{n} to look at`, `{n} ok` (a note is ok); a group of R2's one check shows its detail. Under it, at indent 4, a row for each `fail` and `warn` check: mark, name, detail, HOME's path as `~`. `--json` holds the tool's bytes.
- R6, the suite's rows: an ok row keeps the plan's message; one not ok takes doctor's own fact (also in `--json`). Rows of one step id and one fact fold into one: the id, then `{fact}: {subjects}`. A todo of steps 2 to 5 with no command is counted, not printed (` ({n} waiting on the rest)`); so is step 5's door row while the `door` check is not ok.
- R7, at most one line under a row: a plan row whose line is not `run` prints the plan's labelled line, only when no step 2 to 5 is left; a remedy starting `/` reads `in Claude Code: {remedy}`; another remedy the close does not give reads `fix: {remedy}`. No `run:`.
- R8, the close: `This machine is set up.`, or `{failed} failed, {warned} to look at, {ok} ok.`; then at most one `next: {command}` through `t.hint`: (a) a failing suite row's remedy; (b) the setup command while a step 1 to 5 is not ok; (c) the first failing tool's first failing remedy when a shell line, else its doctor; (d) the first warn row's shell remedy that is not step 6's. A tool's doctor is `cmd.say(<name>, "doctor")` under a door, else its file through `prog.shown`, then `doctor`.
- R9, the `## Doctor` catalogue as the brief's table; `doctor.title`, `.group`, `.run`, `.tool.ok` and the four `hint.doctor.*` leave.
- R10, `--all`, doctor's flag alone: every check a row, nothing folded or left out. R11, `--json` keeps the pin's keys, checks cut to four keys, the counts recounted; `--all` changes no byte of it.

## 3. Interfaces

`doctor.read_answer(code, out) -> [check] | None` (R1); `own_doctors` runs both rounds through `tools.run_all`'s `then`. `cli.DOCTOR_FLAGS = (("--all", None, "all"),)`. The brief's `prog.form(env, lib, tool)` is `prog.form(env, tool)` in the code.

## 4. Acceptance

Each in a temp HOME with a minimal env; a tool is a stub `agentik-<made-up name>` that counts its starts. Measured at 2bf868c by `tests/test_sc10_doctor_checks.py`.

| # | line | at the pin |
|---|---|---|
| 1 | steps 1 to 6 ok, three stubs each answering three ok checks: one line a group and `This machine is set up.`, stderr empty, exit 0 | a line a check; `next: nothing to do` |
| 2 | empty HOME, a stub `claude`: at most 8 lines, none twice, the last `next: ` and the setup command, which exits other than 127 in `sh -c`; exit 0 | 31 lines |
| 3 | a `doctor --json` exiting 0 with a `fail` `root` whose detail D holds HOME, text ending on L: a row with `root` and D under `~`, `--json` holds D whole, no L, exit 1, the hint is that tool's doctor | `its doctor exits 0`, exit 0 |
| 4 | the same stub, exit 2 and no `fail`: exit 0 | `FAIL` and L, exit 1 |
| 5 | two warn checks of one name, no fail: two rows, group warn, exit 0, no hint | not shown |
| 6 | no `schema`; `--json` refused and plain passing; plain printing, exit 1; the same, silent: passed, passed, failed, `failed, and printed nothing`; each started twice, line 3's once | each once |
| 7 | `agentik murmur install-cli` not in the close: `fix:` under its row; `/murmur:install-cli`: `in Claude Code:`, never the hint; no `run:` | `run:` |
| 8 | `--all` in lines 1 to 3: every check of `--json` a row; `--json` byte-equal with and without it, counts a recount | one check a tool |
| 9 | under `## Doctor` no message holds `exit`, `would`, `run:` or `{code}`; none passes 76 characters before its values | three hold `exits` |
| 10 | no `claude`, no `describe`; a stub sleeping past the deadline reads slow inside the pin's bound | one round |
| 11 | `make voice` green, sidecar committed; the suite under `/usr/bin/python3`; `make check` once, last, through the gate queue | |

## 5. Not built

R4's `scope`; a row's width (sc3); the hint's two-line form (sc4); the first screen (sc5); `term.py`, `plan.py`, other screens; a version (phase 2).

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real HOME's files. The report: head sha, gate id and exit, acceptance 1 to 11 at the pin and now.
