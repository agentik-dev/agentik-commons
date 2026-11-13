# Packet su2-screen: the screen of `status`, drawn from one object for a terminal and for a pipe

| item | value |
|---|---|
| from | agentik-hq's brief su2-screen of 2026-11-13, R1 to R12; hq design/18's row su2, its second half (§3.3 items 8, 9, 12), under design/15's look and voice (§5, P3, P6 to P8); level S3 |
| pin | agentik-commons main 7bef66c (suite 0.6.2); worktree `.claude/worktrees/su2-screen`, branch `su2-screen`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; made-up names; no version set |
| may touch | `plugins/suite/lib/agentik_suite/status_screen.py`; `plugins/suite/lib/agentik_suite/term.py` (one new method of `Term`, `grid`); `plugins/suite/lib/agentik_suite/messages.md` (new ids at the end of `## Status`); `tests/test_su2_screen.py`; `tests/fixtures/su2/screen/*`; `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-13-18.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_su2_screen` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

Design and user experience at full depth. This screen is read many times a day, by a person in a terminal and by an agent through a pipe, so the screen is the design: build it to the byte. A second builder works beside this one from the same pin on the read that fills the object (`su2-read`); a join merges the two branches. Touch only the files named here.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names). The screen's bytes are the three states in `tests/fixtures/su2/screen/` (`quiet`, `busy`, `broken`; each `.json`, `.tty.txt` at 80 columns, `.piped.txt`, `.hint.txt`).

- R1, what stands: the packets ak1a, ak1b, ak2-door and su1: the floor, `term` the one writer, the catalogue and its voice, the streams (the screen on stdout, the hint on stderr), no tool's name in the package or its tests. A tool's name reaches the screen only as a value.
- R2, the interface: `status_screen.part(t, obj, name, tool)` draws one part, reading its own part, `at`, `covers`, `hand` and its own sources only; `foot(t, obj, tool)` draws `sources`, `not read` and the hint; `draw(t, obj, tool)` is the five parts in order, then `foot`. It never runs a tool, reads a file or a clock.
- R3, the order: `watchers`, `sessions`, `gate`, `backlog`, `runs`, always all five; then `sources` always and `not read` when `not_read` is not empty, with no mark. A part with nothing to say is one row. No blank line, title, box or rule.
- R4, the grid: the mark, two spaces, the label padded to 8, two spaces, the text; later rows start at the text's column (13 with glyphs, 16 with words). A row of cells pads each cell but the last to the widest of its column in that part, two spaces apart. No row ends in a space.
- R5, the marks: `ok`; `warn` where the part has an entry in `hand`; `note` where its state is `partial` or `not read`, no watcher is declared, or `covers.rule` is `none` (the backlog). `warn` wins. `fail` is never used.
- R6, the cut: on a terminal a row past the width ends at it with `…` (`...` where the stream cannot encode it). Never cut: a row stating an entry of `hand`, a command's row (`start it:`, `see:`), a tool's stderr line. Off a terminal nothing is cut and every byte is ASCII but a value's own.
- R7, the caps: sessions and the gate's jobs (running, queued, red) at most 5 rows; past that, 4 and `and {n} more: agentik {tool} {argv less --json}` from the part's source.
- R8, the styles with colour: the label bold, the mark its colour, dim for a command's row, the beat's line and the foot's text.
- R9, numbers: an age one unit, floored (`s`, `min`, `h`, `d`); a context `k` or `M` with at most one decimal; a source's time seconds to one decimal; a wall drops a trailing zero; `{when}` is `%Y-%m-%d %H:%M` local; one is singular.
- R10, each part's rows and the hint: the brief's R9 and R10, word for word, as catalogue messages under `status.` and `hint.status.`. The hint, one, through `t.hint`, never with `-q`: a hand's count and its first remedy; else `next: {tool} doctor` where a source timed out, was unreadable or changed; else none.
- R11, files: as `may touch`. Not this row's: `status.py`, `cli.py`, `tools.py`, the Help lines, `README.md`, `plugin.json`, `GUIDE.md`, `NICE_TO_HAVE.md`.
- R12, design "the command on screen": `Term.table`, `Term.error` and `Term.hint` unchanged; the command's own name is `{tool}`; every new message at most 76 characters before its values, never `this version`, never an exit code.

## 3. Acceptance

Each in process: a `Term` over two streams held by the test, the terminal one answering `isatty` with no `fileno` (width 80), colour off unless the line says so, `TZ=UTC`. At 7bef66c (measured): `status_screen` does not exist, so every line fails at its import.

| # | line |
|---|---|
| 1 | `draw` of `quiet.json`: on the terminal stream stdout is `quiet.tty.txt` byte for byte, stderr empty; on a pipe `quiet.piped.txt`, stderr empty |
| 2 | `draw` of `busy.json`: `busy.tty.txt` and `busy.piped.txt`, stderr empty; the piped text under 2,048 bytes |
| 3 | `draw` of `broken.json`: `broken.tty.txt` and `broken.piped.txt`; stderr one line, the mark and `broken.hint.txt`'s sentence; with a quiet `Term`, stderr empty |
| 4 | on the terminal no row of the three past 80 characters but a fault, command or stderr row (two in `broken`); at 60 the same with 60; at 200 no `…` |
| 5 | the piped screens: no escape byte, nothing outside ASCII; colour on: labels bold, each mark its colour; `NO_COLOR` set: none |
| 6 | `part` for the five names then `foot` writes `draw`'s bytes for the three; `part` for `watchers` on an object of `at`, `covers`, `watchers`, `hand`, `sources` draws its rows |
| 7 | nine live sessions: four rows, then `and 5 more: agentik crew status`; nine gate jobs: the same with `agentik bench gate status` |
| 8 | one case each for the words the fixtures do not show (the brief's line 8 list) |
| 9 | the hint's four cases, each with what stderr holds |
| 10 | the package's tests stay green: the writer test, the name test, the catalogue's tests |
| 11 | `make voice`, then `make check`, each once through the gate queue, green |

## 4. Not built

The read that fills the object, `--json`, the verb's wiring, the Help lines, the README, the version: the other slice and the join. Rows in flight and what waits on the owner get their own label in a later row.

## 5. The landing

No version is set here: the join of the two slices takes the number. About 65 messages are new, so the coordinator owes a respeak pass over the joined catalogue, then `make voice` again.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real user's Claude Code files. The report: head sha, gate ids and exits, acceptance 1 to 11 at the pin and now, each message reworded for the voice check.
