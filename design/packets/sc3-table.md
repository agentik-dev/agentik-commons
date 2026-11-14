# Packet sc3-table: a table is laid out to the terminal's width, and `COLUMNS` is read

| item | value |
|---|---|
| from | agentik-hq's brief sc3-table of 2026-11-13, R1 to R10, and its start line of 2026-11-14; hq design/23 §2 (F2), §9 (row sc3-table); level S3 |
| pin | agentik-commons main 43e902e (`Merge rp6-verb`, suite 0.7.2); worktree `.claude/worktrees/sc3-table`, branch `sc3-table`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process; made-up names; no test reads the live home or the real terminal's size; no message changes; no version (a phase 2 names it) |
| may touch | `plugins/suite/lib/agentik_suite/term.py` (`Term.table`, `_Stream.width`, `columns`, one helper); `tests/test_sc3_table.py` (new); this packet; `history/sittings/2026-11-14-3.md` |
| verify | `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 9 below; `python3 -m unittest tests.test_sc3_table` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (stdlib at Python 3.9), hq entry 37 (made-up names).

## The owner's words

2026-11-12: "Make it a high quality modern CLI tool that is dynamic and has high quality concise human friendly feedback". And: "Make plugin configuration discoverable and drill down."

## Measured at the pin, on a pty

A temp HOME under `env -i` (HOME, PATH, XDG_CACHE_HOME) with the made-up tool `quill` of 24 keys, the value of `k05` a sentence of 180 characters (the fixture of `tests/test_sc3_table.py`). Each cell: lines, lines past the edge, the longest line.

| screen | at 60 | at 80 |
|---|---|---|
| `config` | 6, 3, 149 | 4, 1, 149 |
| `config quill` | 51, 3, 210 | 51, 3, 210 |
| `doctor` | 10, 2, 116 | 10, 2, 116 |
| `setup --dry-run` | 39, 23, 189 | 32, 15, 189 |

1. The cause is in `Term.table`: each column is as wide as its widest cell, so one long value starts the next column past the edge, and a last cell that does not fit moves under its row at that column's start.
2. `COLUMNS=60` on a terminal changes no byte: the width is `os.get_terminal_size` alone.
3. A pipe gets one line a row and no escape byte; the nine screens of line 7 hash the same with and without `COLUMNS=60`. Both stay.
4. `term.columns` is on main (R2's function): a wide character 2 and a combining mark 0, but a zero-width character (U+200B, U+200D, U+FEFF) 1.
5. su2's `Term.grid` reads its width from `_Stream.width`, so R1 moves `status` with `config`.

## Rulings

- R1, the width of a stream. On a terminal: `COLUMNS` from the command's environment where it is a whole number above 0; else the terminal's own size; else 80. A width under 40 is taken as 40. Off a terminal there is no width, whatever `COLUMNS` holds.
- R2, one function counts columns, `term.columns(text)`, by `unicodedata`: a wide or fullwidth character is 2, a combining mark or a zero-width character 0, any other 1. `table` measures and pads by it, never by `len`. It is at the pin: mended for the zero-width character, by a test red there.
- R3, the columns, on a terminal of width W. Each column but the last is as wide as its widest cell, and never wider than a third of W. The last column takes what is left of W. The fixed indent is the row's own indent plus 4.
- R4, a cell that does not fit its column. A plain cell or a `name` wraps at spaces inside its column, and its later lines start at its column's start; the cells after it stay on the row's first line. A word longer than the column stands whole on a line of its own and is not broken. A `path` cell is never wrapped: where it does not fit, it goes whole on a line of its own under the row, at the fixed indent. An `after` line, which holds a command, does the same: whole, at the fixed indent.
- R5, the last column with under 24 columns left: the last cell goes under the row at the fixed indent and wraps to W from there.
- R6, nothing is cut. No `…` is written by this row.
- R7, so no line `table` writes passes W, but one that holds a single word, path or command longer than its room.
- R8, the paint. Each line of a wrapped cell is painted on its own, so no escape sequence is left open at a line's end, and none is written where colour is off. The status column keeps its place on the row's first line.
- R9, off a terminal: the pin's bytes. One row is one line; nothing wraps or moves.
- R10, the callers. No call of `t.table` changes, and no message. `t.line`, `t.hint` and `t.error` are not this row's: a title or a hint is one message, and the terminal wraps it.

## Acceptance

Lines 1 to 6 draw through `Term.table` on a fake stream that answers `isatty`, its width given by `COLUMNS`. Lines 7 and 8 start the suite in the temp HOME above; the pty is sized before the suite starts.

| # | line | at the pin |
|---|---|---|
| 1 | at 50, 60, 80 and 120 columns, a row of a mark, a name, a sentence of 180 characters and a short last cell: no line passes the width; the last cell is on the row's first line; each word of the sentence is there once, in order | one line, past the width |
| 2 | at 60, a `path` cell of 90 characters in the last column: one line, whole, at the row's indent plus 4; no other line passes the width | at its column's start |
| 3 | at 50, an `after` line holding a command of 70 characters: whole, on one line, at the row's indent plus 4 | at the last column's start |
| 4 | a column of a cell of three wide characters, one of three ASCII letters and one with a combining accent: the next column starts at one terminal column in all three rows; a zero-width character takes none | counted by `len`; U+200B is 1 |
| 5 | on a terminal whose own size is 120 (mocked), `COLUMNS=60` lays the table out at 60; `COLUMNS` unset, empty, `0`, `-5` or `abc` at 120; `COLUMNS=10` at 40; off a terminal `COLUMNS=60` changes nothing | 120 for all |
| 6 | with colour on, each line of a wrapped cell opens and closes its own escape sequence; under `NO_COLOR=1` no escape byte | no wrapped cell |
| 7 | in a pipe, with and without `COLUMNS=60`: bare, `help`, `help issue`, `config`, `config quill`, `config quill.k05`, `doctor`, `setup --dry-run` and `status --check` are byte-equal, with no escape byte, and equal the pin's (hashed in the record) | holds |
| 8 | on a pty at 60 and at 80 columns, the same screens: no line a table writes passes the width, but one that holds a single word, path or command | the table above |
| 9 | the full suite under `/usr/bin/python3` and the PATH `python3`; `make check` once, last, through the gate queue | |

## Interfaces

`_Stream(raw, no_colour, env=None)`: `Term` hands it its `env`, the command's. `_Stream.width()`: R1. `Term._laid(stream, grid, widths, indent, marked, mark_at)`: the table on a terminal; `Term.table` keeps its signature and its off-terminal loop. `term._wrap(text, room)`: R4's lines.

## Not built

A cell cut with `…` and config's own columns (sc6); the picker's frame (sc12); the live line (sc9); a title longer than the terminal; `send.py`'s own `os.get_terminal_size` (rp5's screen on the terminal device, not a table).
