# Packet in4-inbox: `inbox`, one list of what waits on the owner across every checkout

| item | value |
|---|---|
| from | agentik-hq's brief in4-inbox of 2026-11-13, R1 to R17, with the spawn line's amendments A1 to A6 of 2026-11-14; level S3 |
| pin | agentik-commons main 9042a21 (suite 0.7.0); worktree `.claude/worktrees/in4-inbox`, branch `in4-inbox`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; every run in a temp HOME over made-up checkouts; no version |
| may touch | `plugins/suite/lib/agentik_suite/inbox.py`; `plugins/suite/lib/agentik_suite/cli.py` (R15's lines and `_takes`'s clause); `plugins/suite/lib/agentik_suite/messages.md` (`verb.inbox`, `usage.inbox`, `flag.check`, `## Inbox`); `plugins/suite/lib/fallback.json` (one `inbox` list in two rows); `README.md` (one row); `tests/test_in4_inbox.py`; `tests/test_sc4_errors.py` (`MergedVerbsTest`); `design/voice/checked.sha256`; this packet; `history/sittings/*.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 22 below; `python3 -m unittest tests.test_in4_inbox` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 120 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"One owner inbox across every hq." On one day he carried texts between five sittings by hand and had questions open in more than one tree. This verb is the one read of what waits on him: the open questions, and what waits on his hand. He looks at it many times a day, so the screen is the work, its words and order as the brief drew them.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names).

- R1, what stands: ak1a, ak1b, ak2-door, su1, su2-read and the join's packets: the floor, `term` the one writer, the catalogue's voice, the `--json` object, the four exits, no tool's name in the package, its messages or its tests. The verb writes nothing but the describe cache, starts no process but a listed tool's, asks nothing, never loops, opens no file in a checkout for writing and runs no `git`.
- R2, `inbox [REPO...] [NUMBER...] [--check] [--json]`: a noun of ASCII digits with no leading zero is a question's number, any other a path; `--check` with a number exits 2.
- R3, the reads by name: `questions` (`agentik.questions/1`: `repos [{repo, file, questions [{n, title, line, state, why, proposed, recommended, text}], answered, decided {count, newest}}]`, `skipped [{repo, why}]`), `charter` (`agentik.charter/1`: `repos [{repo, file, name, mtime, closed, next_act, waits}]`, `skipped`), `backlog` (no schema: `repos [{repo, handoff, steps [{n, title, line, level, state}]}]`, `skipped [path]`). A schema above 1 or a missing named key is `unknown`.
- R4, the calls: `questions` and `charter` one call each with every checkout after the argv, `backlog` one a checkout; all through one `tools.run_all` under a 5 s wall. A checkout that is no folder or cannot be listed goes to no tool; an answer's repo is matched by `os.path.realpath`.
- R5, `_reads(cmd)`: the table's rows whose tool is on PATH, in name order, then the `status` reads of the other tools' `describe` answers (`tools.describe_all`); a tool with a row is never asked `describe`. The table holds the reads in a list `inbox` of `{name, argv}`, not in `status` (see 4).
- R6, the checkouts: `covers.covers`, then the inbox's own two steps: under `args` a second naming of one folder is dropped; under the user file's list an entry neither absolute nor under `~/` is left out with one stderr note. Rule `none` exits 2.
- R7, a call that gave no answer: `no_tool`, `no_answer`, `timed_out`, `unknown`; `backlog`'s said once where every call ended in one state, else once a checkout. A checkout a read skips draws nothing from it.
- R8, what waits: each `open` question, each line of `waits`, each step waiting on the owner; `complete` when every call answered and every checkout was read.
- R9 to R12, the list, the hint, `--check` and a number: the brief's screens, words and order.
- R13, `--json`: `agentik.inbox/1` with `covers`, `count`, `complete`, `reads`, `checkouts`; `check` and `lines` with `--check`; `opened` with a number. The exit is the text's.
- R14, the exits: 0 when it ran; 1 only under `--check`; 2 usage, a bad user file, no checkout, an unknown number; 3 when no command on PATH gives any of the three reads.
- R15, `cli.py`: `inbox` in the import, last in `VERBS`, `VERB_FLAGS["inbox"] = STATUS_FLAGS`, `do_inbox` last; `_takes` gains `inbox`'s clause, since sc4's `offer` refuses a line of a verb it does not know.
- A2, A3: a refusal is a `Refusal`, the cause then `next:` and a line that runs; a file that does not parse has no `next:`; each hint starts `next:`; every command comes from `cmd.say` or `cmd.slots()`.

## 3. Acceptance

Each in `Home`, `TZ=UTC`, two made-up tools on the stub PATH, four made-up checkouts under a temp folder. At 9042a21 (measured) every run of the verb prints `inbox is not a verb or a tool` and `next:` the help line, exit 2.

| # | line |
|---|---|
| 1 | two checkouts piped: exit 0, the first screen byte for byte, one hint, no escape byte |
| 2 | under a pty of 80 columns: glyphs, the sitting line cut with `…`, no line past 79, the name bold |
| 3 | nothing waiting; a checkout that is no folder: `not read: not a directory`, `at least` |
| 4 | `fig-hq`: answered, a bare hand line, decided, the sitting; with `waits` null, `with no Waits part` |
| 5 | an `unreadable` question: its `why` shown, not counted, not in `--check` |
| 6 | the charter read exits 2, answers `charter/2`, sleeps past the wall (back in 6 s, gone), is off PATH |
| 7 | a backlog answer with no `state` for one checkout of two, then for both |
| 8 | no tool on PATH: exit 3, the refusal, stdout empty |
| 9 | `--check`: the check screen exit 1; nothing exit 0; a read with no answer first |
| 10 | `--json`, then with `--check` |
| 11 | a number: the block as written; an unknown number; `--check 1`; two checkouts |
| 12 | the user file's list with a relative entry; a tab in it |
| 13 | rule `hq` from a sibling; rule `cwd`; no repo: exit 2 |
| 15 | the recorded argv: one call each for two reads, one a checkout for the third |
| 16 | each table row's `inbox` list run as its argv, no `describe` |
| 17 | after every run, each checkout's every entry and `git status` as before; HOME unchanged but the cache |
| 18 | `help`, `help inbox`, `status --check --help`: `inbox` and the new `flag.check` |
| 19 | the checkouts read-only: the first screen |
| 20 | two other folder names: the first screen with those names alone changed |
| 21 | the name greps and `scripts/hygiene --require-private`: clean |
| 22 | `make voice`, then `make check`, each once through the gate queue, green |

Line 14 is in 13. MergedVerbsTest gains `inbox`'s mistyped lines.

## 4. Where this differs from the brief

- R5's three reads go in a list `inbox` of each row, not in `status`: in `status` they make su2-read's `TableTest` look up a fixture it does not have, and add two `not drawn` rows to the status screen. The coordinator may move them once `status` draws them.
- `covers.covers` stands for R6's seam: its `checkouts` rule is R6's `user`, and where the cwd's repo and a sibling both declare `kind: hq` it takes the cwd's repo, not the first by name. Kept as main has it.
- A refusal is sc4's two lines; the brief's one-sentence errors are cut to their cause.

## 5. Not built

Lines between sittings; `inbox answer`; a hook that calls `--check`; a cache of any read; a live view; the status screen's count of these reads. No version: phase 2 takes it.
