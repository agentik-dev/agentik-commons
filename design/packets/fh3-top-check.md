# Packet fh3-top-check: `scripts/readme-top` holds a README's first lines to the ten-line form

| item | value |
|---|---|
| from | agentik-hq's brief fh3-top-check of 2026-11-15, R1 to R8; level S4 |
| pin | agentik-commons main c3eaf91 (suite 0.7.24); worktree `.claude/worktrees/fh3-top-check`, branch `fh3-top-check`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync run on a tool; no bare `make`; no relay verb or binary; no `claude` process, no agent; made-up tool names in fixtures; no version set |
| may touch | `scripts/readme-top` (new), `tests/test_readme_top.py` (new), `tests/test_sync.py`, `scripts/sync`, `Makefile`, `README.md`, `GUIDE.md` (§10's "README shape" row), this packet |
| verify | `make check` once, last, through the gate queue, `--wait` |
| acceptance | 1 to 7 below; verify green |

## 1. The owner's words

A README's top, the lines before its first `##`, is one form (GUIDE §10): a person reads those lines and decides. Nothing holds the form, and a count of lines alone would not: measured before the form was written, six tops of two to six counted lines each, five with no fenced block, one whose block held one line, none with a "Use it when" sentence.

## 2. Rulings

- R1, `scripts/readme-top [FILE...]`: stdlib Python, `#!/usr/bin/env python3`. With no FILE it reads `README.md` in the cwd. The top is every line before the first line that starts `## `; a file with no such line is read whole.
- R2, four tests, each its own finding, in this order. Lines: a line counts unless it is blank, a fence marker (starts with three backticks) or starts `<img `; a line inside the fence counts; more than ten is a finding. The block: exactly one fenced block, holding exactly two lines. The sentence: exactly one line starts `Use it when `. The link: at least one `](https://github.com/agentik-dev)`; a longer address under it does not count.
- R3, output: one finding a line on stdout, `<file>: top: <what>`, the file as given. In the form: `<file>: top: <n> lines, in the form`.
- R4, exits: 0 every file in the form; 1 a finding; 2 usage or a file that cannot be read, one line on stderr naming it. `-h` and `--help` print the docstring, exit 0. No other flag.
- R5, `Makefile`'s `lint` gains one line running `scripts/readme-top`.
- R6, `scripts/sync` copies the script into `<repo>/scripts/` and lists it in `vendored.sha256`, after `recordlint`; it adds no line to a tool's Makefile.
- R7, `README.md`'s "What it holds" table gains a row; GUIDE §10's "README shape" row gains the clause "`scripts/readme-top` holds a README to it".
- R8, nothing under `plugins/` changes; no version.
- Not this row's: any tool repo, the lines of a README's top, `scripts/hygiene`.

## 3. Acceptance

Fixtures are made-up tops for made-up tools, written in the test file; no test reads a sibling checkout.

| # | line | at the pin |
|---|---|---|
| 1 | `tests/test_readme_top.py`: six tops in the form pass, exit 0, each with its count (an `<img ` line under the title; exactly ten counted lines; a block that is a slash command; a fence with a language word; a second link to another address; no `##` after it) | no script |
| 2 | six failing tops, each exit 1 with the one finding named (no block; a block of one line; two blocks; eleven lines; no `Use it when `; a link only to a longer address) | no script |
| 3 | a top with three faults prints three lines in R2's order, exit 1; two files, one in the form, print a line each, exit 1 | no script |
| 4 | a path that is no file: exit 2, one stderr line, empty stdout; `--help` exit 0; `--json` exit 2 | no script |
| 5 | `scripts/readme-top` at the worktree root prints `README.md: top: 8 lines, in the form`, exit 0 | by hand: 8 counted lines, one block of two lines, one sentence, one link |
| 6 | `tests/test_sync.py`: after `sync` into a made-up repo, `scripts/readme-top` is there, executable, listed in `scripts/vendored.sha256` | not copied |
| 7 | `make check` green through the gate queue | green |

## 4. Not built

Each tool's sync and its one gate line, after that tool's own top row; the tops themselves.
