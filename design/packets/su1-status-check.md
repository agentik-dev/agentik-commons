# Packet su1: `status --check`, a declared watcher that is not running said in one line

| item | value |
|---|---|
| from | agentik-hq's brief su1 of 2026-11-13, R1 to R11; hq design/18's row su1 (§3.2 items 5 and 7, §6); level S3 |
| pin | agentik-commons main 2ccedb1 (`Merge ak1b-config`, suite 0.3.0); worktree `.claude/worktrees/su1-status-check`, branch `su1-status-check`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no ledger; every run in a temp HOME; made-up names in fixtures |
| may touch | `plugins/suite/**`; `tests/test_su1_status_check.py`; `tests/test_agentik_suite.py` (its stdlib set alone); `design/voice/checked.sha256`; `README.md`; `NICE_TO_HAVE.md`; this packet; `history/sittings/2026-11-13-6.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_su1_status_check` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first, the version bump last; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

None bind this row. A watcher was off for 8.7 days and nothing said so. This check names each declared watcher that is not running. A session's start hook will call it, so it is quick and silent when all run.

## 2. Rulings

The repo keeps no `DECISIONS.md`. Cited: hq entry 6 (`/usr/bin/python3` at a 3.9 floor, the standard library alone) and hq entry 37 (made-up names).

- R1, what stands: the packets ak1a and ak1b: the floor, `term` the one writer, `messages.md` and its voice (the result, the fact, the next command), the grammar, the streams, the `--json` object, the four exits, no tool's name in the package, its messages or its tests. New: `status.py`, `tests/test_su1_status_check.py`, the catalogue's last section `## Status`. The check runs no tool and no `describe`, reads no cache, starts one process at most, `ps`, and is back in under 2 s.
- R2, the verb: `status --check [--ps FILE] [--now ISO]`. `status` without `--check` exits 2 and says this version only checks. `--check` is `status`'s alone. `--ps` and `--now` are test hooks, the parser's first flags with a value: one table beside `VERB_FLAGS`, read as `--ps FILE` and `--ps=FILE`; a missing value is `_bad_flag`'s. `--ps FILE` is a saved listing in place of `ps`; `--now ISO` the clock: ISO 8601 with `Z`, an offset, or neither (local). An unreadable file, or a value that is no time, exits 2.
- R3, the declaration: the user file alone, `settings.read(settings.user_path(env))`. A watcher is a name with `match` and `start`, optionally `beat` and `writer`, each a string. A file outside the subset, or `watchers` that is no mapping of mappings: exit 2, file and line on stderr, stdout empty. No file or no watcher: exit 0, nothing. A watcher with no `match` or no `start` is not checked: one stderr note names it and the file; no exit changes.
- R4, the listing: `/bin/ps -axo pid,ppid,uid,etime,command`, else `ps` on PATH, under a 1 s wall, its group killed past it. The first line is the head; a row is four fields, then the command. No listing (the wall, a non-zero exit, no `ps`): every watcher is `unknown`.
- R5, the match: `match` splits on blanks into a program and its words. A process counts when its uid is the reader's and its command, split on blanks, has the program as its head and the words directly after it, in order. The head is the first word; where its basename begins `python` or is `sh`, `bash`, `zsh`, `dash` or `env`, the head is the first later word that is none of these: a word beginning `-`, the word after `-X`, `-W`, `-o` or `-u`, an assignment. A `-c` or `-m` on the way means no match. The head counts by its basename and, as a link, by its target's.
- R6, the beat: the file `beat` names (a leading `~/` is HOME; another relative path is no beat), one JSON object with `at` (epoch seconds) and `fresh_s`, finite numbers, optionally `writer` and `line`. Anything else is no beat. Its age is now less `at`, never below 0. It is the watcher's own when no `writer` is declared, or the two are equal.
- R7, the states: `running` (a process; no beat or a beat within its `fresh_s`, whoever wrote it), `hung` (a process; a beat older than its `fresh_s`), `missing` (no process), `unknown` (no listing). `since` is the beat's `at`, only when the beat is its own, shown local `YYYY-MM-DD HH:MM`.
- R8, the lines: one on stdout for each watcher not `running`, in the file's order, plain, through `term`; exit 1 when there is a line, else 0 and nothing: `<name>: not running[ since <when>]; start it: <start>`, `<name>: running but silent[ since <when>]; start it: <start>`, `<name>: not checked: ps gave no listing`.
- R9, `--json`: `schema` `agentik.status/1`, `ok` true, `check` true, `watchers: [{name, state, pid, since, beat_writer, beat_line, start}]`, every checked watcher; `since` epoch seconds or null; `beat_line` the beat's `line` when its own and fresh. The exit is the text's.
- R10, the summaries: `setting.watcher.match` the program and the words after it that find the watcher's process; `.start` the line that starts it; `.beat` the file it writes while it runs; `.writer` the name a beat must carry to count as its own.
- R11: `help` and the README list `status`; `GUIDE.md` stays.

## 3. Acceptance

Each in ak1b's `ConfigHome` with `TZ=UTC`, a user file declaring `lamp` (`match: lampd watch`, `start: lampd watch --every 60`, a `beat` path, `writer: watch`), a `--ps` file under the test's uid, `--now 2026-11-13T12:00:00Z`. At 2ccedb1 (measured): lines 1 to 9 print `status is not a verb. Run agentik-suite --help for the list.`, exit 2; line 9's card reads `How often the watcher looks.`

| # | line |
|---|---|
| 1 | no `lampd` row, beat `{"at": 1793799937, "fresh_s": 180, "writer": "watch"}`: `lamp: not running since 2026-11-04 13:45; start it: lampd watch --every 60`, exit 1; writer `report`, or the file absent or not JSON: the line without `since` |
| 2 | each row alone reads missing: `/bin/sh -c lampd watch`, `grep lampd watch`, `otherd wait lampd watch`, `python3 -c lampd watch`, `lampd`, `lampd report watch`, `/opt/bin/lampd watch` under another uid |
| 3 | no beat declared, each row running, exit 0, stdout empty: `/opt/bin/lampd watch --every 60`, `/opt/py/bin/python3 /opt/bin/lampd watch`, `/usr/bin/python3 -I -X pycache_prefix=/c /opt/lib/lampd watch`, a link `oldlamp` to `lampd` |
| 4 | a beat 100 s old (`fresh_s` 180): running, either writer; 600 s old by `watch`: `lamp: running but silent since 2026-11-13 11:50; start it: lampd watch --every 60`, exit 1; by `report` without `since`; an `at` after now: running |
| 5 | two watchers, one running, one missing: one line; no user file, or `checkouts` alone: exit 0, both streams empty |
| 6 | a tab: exit 2, file and line on stderr, stdout empty; a watcher with no `start` beside a running one: exit 0, one stderr note; with `-q` none |
| 7 | `--json` for 1 and 4: one object as R9, the same exits |
| 8 | no `--ps`: the real listing, under 2 s, no watcher `unknown`; in process, a `ps` stand-in sleeping 10 s: `lamp: not checked: ps gave no listing`, exit 1, inside 2 s, the stand-in gone |
| 9 | `status` alone exit 2 naming `--check`; `--now soon` and an absent `--ps` file exit 2; `help` lists `status`; `config suite.watchers.lamp.beat` prints R10's words |
| 10 | after each line HOME outside `$XDG_CACHE_HOME/agentik/` unchanged, no `suite/` cache folder, the stubs `claude` and `agentik-demo` recorded no call |
| 11 | `make check` green after `make voice` |

## 4. Not built

`status` as a read of the tools (the next row); the hook that calls this; a `doctor` check; starting a watcher.

## 5. The landing

`plugins/suite/.claude-plugin/plugin.json` to `0.5.0`, alone in the last commit that touches `plugins/suite/`; nothing checks this bump. More than ten messages are new, so the coordinator owes one respeak pass over the catalogue before the landing, then `make voice` again.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real user file. The report: head sha, gate ids and exits, acceptance 1 to 11 at the pin and now.
