# Packet su2-read: `status` reads five sources at once and gives one `agentik.status/1` object

| item | value |
|---|---|
| from | agentik-hq's brief su2-read of 2026-11-13, R1 to R12 and J1 to J4; level S3 |
| pin | agentik-commons main 7bef66c (suite 0.6.2); worktree `.claude/worktrees/su2-read`, branch `su2-read`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, install or sync; a merge only at J1; no bare `make`; no relay verb or binary, the fifth read a stub in every test; no `claude` process, no agent; every run in a temp HOME; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/status_read.py`; `plugins/suite/lib/agentik_suite/covers.py`; `plugins/suite/lib/agentik_suite/status.py`; `plugins/suite/lib/agentik_suite/tools.py`; `plugins/suite/lib/fallback.json`; `plugins/suite/lib/agentik_suite/messages.md` (`err.status.path`); `tests/test_su2_read.py`; `tests/fixtures/su2/read/`; `tests/test_su1_status_check.py` (the line pinning the old key set); `design/voice/checked.sha256`; this packet; `history/sittings/*.md`; at J3 alone `cli.py`, `README.md`, `plugin.json` and the Help lines |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 12 below; `python3 -m unittest tests.test_su2_read` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

Design and user experience at full depth: this read is what a person looks at many times a day, and what an agent reads through a pipe. Four reads became one because a watcher was off for 8.7 days and nothing said so; so this read never drops a source in silence and never guesses. `su2-screen` draws the object from saved copies beside this row; on the coordinator's word this branch joins it.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names).

The object: `schema`, `ok`, `check` false, `at`, `ms`, `covers {rule, hq, checkouts}`, `watchers`, `sessions {state, checked, window_min, live, ended, past_window}`, `gate {state, runner, running, queued, last, red}`, `backlog {state, open, first, items, checkouts, skipped}`, `runs {state, shown, aged}`, `hand [{part, kind, name, remedy}]`, `sources [{name, tool, argv, state, ms, exit, stderr, wall_s}]`, `not_read` `["owner", "rows"]`. A part's state: `ok`, `hand`, `partial`, `not read`; `hand` wins. A value a source did not give is null; the object holds no sentence.

- R1, what stands: ak1a, ak1b, ak2-door, su1: the floor, `term` the one writer, the catalogue's voice, P4's `--json`, the four exits, no tool's name in the package or its tests (a tool is named in `fallback.json` alone).
- R2, the verb: `status [<path>...] [--json] [--ps FILE] [--now ISO]`; a path that is no folder is exit 2, `err.status.path`, code `bad_path`; `--check` with a path stays exit 2. Before the join, `status` without `--json` keeps `err.status.check`. The read exits 0 whenever it ran.
- R3, the sources: each row of `fallback.json` gains `status`, a list of `{name, argv[, wall_s]}`: `agents` takes `sessions`; `session` takes `gate` and `unattended`; `decisions` takes `backlog`; `relay` takes `run` (`wall_s` 2.5). A row's tool is never asked `describe`; with no `agentik-<name>` on PATH its reads are `not installed`. Any other `agentik-*` is asked through ak1b's cache, its `status` reads joining the jobs as it answers. A read whose name no part has, or that an earlier tool gave, is `not drawn` and never run.
- R4, the run: one `tools.run_all` holds every read, describe and `ps`. New keywords: `walls` (a job's own seconds), `errs` (stderr to 4 KiB), `times` (seconds to its end); without them it returns what it did. Walls: 1.0 s, a row's `wall_s` where it has one.
- R5, a source's state: `ok`, `not installed`, `timed out` (`ms` its wall), `unreadable` (non-zero exit, no JSON object but the bare `null`, past `tools.CAP`; `stderr` its first non-empty line, 300 characters), `changed` (a pinned key missing or of another kind, or a `schema` above 1; its values null), `not drawn`.
- R6, `covers.covers(env, cwd, paths)`, first match: `args`; the user file's `checkouts`; `hq` (the cwd's repo or a sibling checkout declaring `kind: hq`, then every checkout of that folder by name); `cwd`; `none`.
- R7, the parts and their pins: `sessions` (the one top-level list; seats live by a `claude` process naming their id; helpers counted by state; `past_window`), `gate` (`last`, `red`, `est_s`, `runner.alive`, `no_runner`), `backlog` (argv plus `--order <hq>/HANDOFF.md` and each checkout; not run under `none`), `runs` (`run` and `unattended`; shown while running or of today or yesterday; `run_gone`), `watchers` (su1's check).
- R8, `hand` in the order watchers, gate, runs; a read's remedy is `agentik <tool> <argv less --json>`.
- R9, su1 mended: `_wrapper` compares the basename in lower case; `check` returns `writer` and `beat_at`; `--check`'s lines and exits do not move.
- R10, `status_read.compose(cmd, paths, now, ps_text, on_part=None)`; `PARTS` in that order; `on_part(name, obj)` once a part, as soon as it and every part before it are settled.
- R11, it writes nothing but the bytecode and describe caches.
- R12, `err.status.path` is the cause alone; a usage remedy names `cmd.tool`; a `hand` remedy names `agentik`; every message holds the voice of design "the command on screen".

## 3. Acceptance

Each in su1's `StatusHome`, `TZ=UTC`, `--now 2026-11-13T12:00:00Z`, `--ps` the fixture listing; a stub `agentik-demo` answering `describe.json` and each read with a fixture. At 7bef66c (measured): `status --json` exit 2 `check_only`; `status <path> --json` exit 2 `extra_word` ("takes no argument").

| # | line |
|---|---|
| 1 | `status --json`, the base case: exit 0, one object equal to `e2e.json` but for the times and `covers.checkouts`; one `describe`, no `weather` call |
| 2 | again: no `describe` (the cache); HOME unchanged outside the cache |
| 3 | sessions: a bare `claude` row keeps `acme-old` live with a null pid; the head alone: `ended` 3; no listing: `checked` false, the part `partial`, `watcher_unknown` |
| 4 | gate: no runner, or the runner gone: `no_runner`, remedy `agentik demo gate status`; empty: `ok` |
| 5 | runs: `run_gone`; alive; the unattended run shown; none shown |
| 6 | covers, a case a rule; `status nosuchdir --json` exit 2, `bad_path` |
| 7 | a failing source: exit 3, `[1,`, a sleep past the wall (back in 1.6 s, nothing left), a missing pin, a schema `x/2`; exit 0, no traceback |
| 8 | the table: a stub a row, five `ok`, no `describe`; none: five `not installed`, back in 0.5 s |
| 9 | `on_part`: once a part, in order; the backlog 0.5 s before a slow `run` |
| 10 | `--check` with a `Python.app` interpreter: running; `writer`, `beat_at` in `--json` |
| 11 | a tab in the user file: exit 2; `run_all` as `config` calls it unchanged |
| 12 | `make voice`, then `make check`, each once through the gate queue, green |

## 4. Not built

The screen (`su2-screen`); rows in flight and the owner's waits (`not_read`); a caller or queue time of a gate entry, a pid for the unattended run; `--watch`; the table's removal.

## 5. The landing

No version here: the join takes it (0.7.0 expected) in its last commit under `plugins/suite/`, and the coordinator owes one respeak pass over the joined catalogue.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, a relay ledger, the private hygiene list. The report: head sha, gate ids and exits, acceptance 1 to 12 at the pin and now.

## 7. The join (on the coordinator's word, 2026-11-13)

`su2-screen` merged into this branch; no merge of main and no version here (phase 2 takes 0.7.0). Rulings beyond J1 to J4:

- `status` with no `--json` composes with an `on_part` that draws the part through `status_screen.part` and flushes, then `status_screen.foot`. A stdout closed while it draws raises inside `run_all`, so every read ends; exit 141 (128 plus SIGPIPE), no traceback. An interrupt: 130, as before.
- Each `run_gone` entry of `hand` carries the run's `tool`; the screen matches a gone run by tool and id.
- The screen words the top-level `fault` once, in the watchers part, with a warn mark: `status.fault.listing` and `.parts` for `bad_listing`, `status.fault.unknown` for any other; under it a watcher reads `status.watcher.unchecked` and the sessions part drops `status.unchecked`.
- A source's `fields` is left to `--json`: the screen's sample has no place for it.
- `err.status.check` leaves with its test; `verb.status` and `usage.status` as J3.

| # | line, the join |
|---|---|
| J-2 | `status` piped in the base case equals `e2e.piped.txt` but for its `sources` row's numbers |
| J-3 | `gate-no-runner.json`: the gate's row and one hint naming `agentik demo gate status`; `-q`, none |
| J-4 | `help status` prints the new usage; the catalogue holds J3's `verb.status` and no `err.status.check` |
| J-5 | a `run` read sleeping 0.8 s: the backlog's first row at least 0.5 s before the runs' |
| J-7 | a terminal at 40, 80, 120 columns: no row past the width but a command's; at 120 the piped rows |
| J-8 | `bad_listing`: its two rows once, `warn` on watchers, `note` on sessions, gate and runs |
| J-9 | a closed pipe or an interrupt while it draws: back inside 2 s, the slow read and its child gone |
