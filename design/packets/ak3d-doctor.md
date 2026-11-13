# Packet ak3d: `doctor`, the machine checked in one read, the door's version first

| item | value |
|---|---|
| from | agentik-hq's brief ak3d of 2026-11-13, R1 to R7; hq design/15's row ak3, its second half; level S3 |
| pin | agentik-commons main d795d4a (suite 0.5.0); worktree `.claude/worktrees/ak3d-doctor`, branch `ak3d-doctor`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no ledger; every run in a temp HOME; made-up names in fixtures |
| may touch | `plugins/suite/lib/agentik_suite/doctor.py` (new); `plugins/suite/lib/agentik_suite/cli.py` and `messages.md` (R7's lines alone); `tests/test_ak3d_doctor.py` (new); `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-13-10.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 10 below; `python3 -m unittest tests.test_ak3d_doctor` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"I want to use it today." Three builders work beside you from the same pin, on the suite's `install-cli`, on `setup` applied and on a probe; a join merges the four branches. So you touch only the files named here, and in a shared file only the lines named.

## 2. Rulings

The repo keeps no `DECISIONS.md` and no `CLAUDE.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names in fixtures and the packet).

- R1, what stands. The packets ak1a, ak1b, ak2-door and su1 bind this row: the floor, `term` the one writer, `messages.md` and its voice (the result, the fact, the next command), the streams, the `--json` object, the four exits, no tool's name in the package, its messages or its tests. New: the module `plugins/suite/lib/agentik_suite/doctor.py`, the tests `tests/test_ak3d_doctor.py`, the catalogue's last section `## Doctor`.
- R2, the verb: `doctor`, a read. It takes no word after it. A check is `{name, status, detail, remedy}`; `status` is `ok`, `note`, `warn` or `fail`; `remedy` is a command or null. Checks are grouped by tool, the suite's first. Exit 1 when any check is `fail`, else 0: a `warn` never changes the exit. It reads no cached answer, runs no `describe` and no `claude`, and writes nothing itself.
- R3, the suite's checks, in this order.
  - `door`. The door is the first `agentik` on PATH that is a regular executable file; a FIFO or a folder of that name is passed over, never opened. Its `VERSION` (`agentik_install.read_launcher`) is compared, by `agentik_install.order`, with this command's own door (`agentik_install._source()`'s third path). Older, with the suite's launcher on PATH: `fail`, since the door hands this command no verb; remedy `<tool> install-cli`. Older, with no such launcher: `warn`. No version to read: `warn`. Equal or newer: `ok`. No door on PATH: `warn`, remedy `<tool> setup`.
  - `shadow`. One `fail` for each `agentik-<word>` on PATH (`cmd._on_path()`) whose word is a verb of `VERBS` or one of `remove`, `update`, `init`, `completion`, `inbox`: the door runs that file in place of the suite's verb. The detail names the file. None: one `ok`.
  - `settings`. The user file read by `status.declared(env)`. A `Fault`: `fail`, the file and line in the detail. Each watcher it returns as unchecked: one `warn` naming it and the two keys it needs. Else `ok`; no file is `ok` too.
  - The plan's rows. `plan.build` for the default set, steps 1 to 6, one check a row, named by the row's `id` and subject, the detail the row's own message. `ok` is `ok`; `blocked` is `fail`; `todo` is `warn` with the remedy `<tool> setup`. Step 6's remedy is its own `add` line. Step 7's rows are left out.
- R4, each tool's own doctor. For each entry of `tools.listed` with an executable, but the suite: run `<exe> doctor`, every one at once, through `tools.run_all` with a deadline 30 s from the start. One check, `doctor`, in that tool's group. Exit 0: `ok`. Another exit: `fail`, the detail the last line of its stdout that is not blank, the remedy `<exe's name> doctor`. `timed out`: `warn`. `unreadable`: `warn`. A plugin listed with no executable: `note`. A tool's doctor may write its own state; that is the tool's.
- R5, the lines: one title, then each group, a line for the tool's name and a table of its checks, each row its mark, its name and its detail, the remedy on the line under it as `run: <remedy>`. The close is one hint: when nothing failed and nothing warned, that the machine is set up; when a `warn` names setup, `<tool> setup`; when a check failed, that the `run:` lines above mend it. `-q` gives no hint.
- R6, `--json`: `schema` `agentik.doctor/1`, `ok` true, `failed` (a count), `warned` (a count), `tools: [{name, checks: [{name, status, detail, remedy}]}]`. The exit is the text's. The probe beside you reads these keys.
- R7, shared files, these lines and no other. `cli.py`: `doctor` appended to `VERBS`, `doctor` added to the package import, a method `do_doctor` as the class's last; leave the module's docstring to the join. `messages.md`: `verb.doctor` and `usage.doctor` at the end of their runs in `## Help`, and `## Doctor` as the file's last section. Not yours: `plan.py`, `tools.py`, `status.py`, `tests/test_agentik_suite.py`, `README.md`, `plugin.json`, `GUIDE.md`, `NICE_TO_HAVE.md`, the `Makefile`. Stay inside the standard-library set `tests/test_agentik_suite.py` names.

## 3. Acceptance

Each in `Home` or `ConfigHome`, a stub `claude` that records its calls, every tool made up. Measured at `d795d4a`: `doctor` and `doctor --json` print `doctor is not a verb. Run agentik-suite --help for the list.`, exit 2. In a temp HOME holding the real default set, one tool's own `doctor` exits 2 outside a session with the last line `doctor: failing: resolved, meter`, and the other two exit 0: so line 5's `fail` is what a new machine shows until that tool is mended.

| # | line |
|---|---|
| 1 | empty HOME: exit 0; the suite's group holds `door`, `shadow`, `settings` and the plan's rows; the marketplace's row is `warn` with the remedy `agentik-suite setup`; the hint names `agentik-suite setup` |
| 2 | no `claude` on PATH: its row is `fail`, exit 1 |
| 3 | `~/.local/bin` first on PATH, holding an executable `agentik` with `VERSION=0.1.0` and a made-up `agentik-suite` launcher: `door` is `fail` with the remedy `agentik-suite install-cli`, exit 1. The door at `0.2.0`: `ok`. The old door with no launcher: `warn`, and the exit is not from it. A FIFO named `agentik` first on PATH: back inside 5 s, and the next door on PATH is the one read |
| 4 | a stub `agentik-setup` on PATH: `shadow` is `fail` and names its path, exit 1; a stub `agentik-alpha`: no `shadow` fail |
| 5 | stubs: `agentik-alpha`, whose `doctor` exits 0: `ok`; `agentik-beta`, whose `doctor` prints two lines and exits 2: `fail`, the detail its last line, the remedy `agentik-beta doctor`, exit 1; in process, with the deadline shortened, `agentik-slow` that sleeps: `warn`, inside the deadline, its group gone |
| 6 | a tab in the user file: `settings` is `fail` with the file and line, exit 1. A watcher with no `start` beside a whole one: `warn` naming it, exit 0 |
| 7 | `--json` for lines 1, 3 and 5: one object as R6, the same exits; piped, no escape byte |
| 8 | `doctor extra` exits 2; `help` lists `doctor`; `doctor --help` prints its usage; `-q` prints no hint |
| 9 | after lines 1 to 4 and 6: HOME outside the cache is unchanged, no `suite/` cache folder exists, and the stub `claude` recorded no call |
| 10 | `make voice`, then `make check`, each once through the gate queue, green |

Write the tests of lines 1 to 9 first and see each fail.

## 4. Not built

A tool's `doctor` read under `describe` (the plug's rows; then R4 reads its checks and this fallback goes). A check of two tools claiming one verb, and of a `describe` schema the suite does not know. A watcher check: `status --check` is that. Mending anything: `doctor` reads. The suite's `install-cli`, `setup` applied, a probe (the rows beside you). The README and the version: the join.

No fork for the owner. More than ten messages are new, so the coordinator owes one respeak pass over the catalogue after the join; the builder starts no agent.

## 5. The landing

No landing and no install in this row: the join merges the four branches and lands once. `plugin.json` stays at 0.5.0; the join takes 0.6.0.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real user file. No test runs the real `claude` or a real tool, or writes under the real home. The report: head sha, gate ids and exits, acceptance 1 to 10 at the pin and now.
