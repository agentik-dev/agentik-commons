# Packet sc13-door: the `agentik` command hands every line it has no tool for to the suite, finds the suite beside itself, and prints one version

| item | value |
|---|---|
| from | agentik-hq's brief sc13-door of 2026-11-13, R1 to R7, acceptance 1 to 11, and the coordinator's start line of 2026-11-14 (main took sc2-name, sc4-errors, su2 and rp6-verb since the brief was cut); level S3 |
| pin | main at 43e902e (suite 0.7.2, door 0.2.0, 99 lines, the two doors byte-equal); worktree `.claude/worktrees/sc13-door`, branch `sc13-door`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no test starts `git` for real, reaches the network or reads the live home; made-up names; no suite version and no message of the catalogue changed (in4-inbox and sc3-table build beside this row) |
| may touch | `bin/agentik`, `plugins/suite/bin/agentik` (the same bytes); `tests/test_door.py`; `GUIDE.md` §10's rows `front door` and `exit codes`; the README's one line on the door; the door's older tests that hold its 0.2.0 lines (`tests/test_agentik.py`, `tests/test_ak2b_reach.py`, `tests/test_door_probe.py`), only where a ruling changes the line they hold; this packet; `history/sittings/2026-11-14-3.md` |
| verify | `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_door` OK |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. What a person meets at the pin

Measured at 43e902e in a temp HOME, the door beside a copy of the suite's plugin:

1. `agentik --version` prints `agentik 0.2.0`; `agentik version` prints `agentik 0.7.2`.
2. Each of `--version --json`, `--json`, `--no-color doctor`, `help --json`, `help doctor extra`, `--help --version`, `Config` prints the usage line `usage: agentik <tool> [args...] | agentik help [<tool>] | agentik --version` and exits 2. The suite by its own name answers the first five, and gives the last two sc4's two lines (`--version takes no verb and no --help`, `next: agentik --version`; `Config is not a verb`, `next: agentik config`).
3. Bare `agentik` runs `agentik-suite help`. `agentik-suite` with no argument prints its help screen and exits 0, the same screen as `help`.
4. With the door's folder off PATH and the suite in it, `<folder>/agentik doctor` prints `agentik: doctor is not installed here; agentik-commons/setup sets the suite up`, exit 3.
5. With no suite anywhere, the same line; `agentik-commons/setup` exits 127 from any folder but the one above a clone.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 37 (made-up names). "A tool for a word" is an executable file `agentik-<word>`; "the suite" is `agentik-suite`.

- R1, where the door looks. PATH first, the first match winning, as at the pin. Then, where the door was started by a path that holds a `/`, its own folder. Both hold for a tool and for the suite. The door execs the file it found by that file's path.
- R2, the order. (a) No word: the suite with no word; with no suite, the list. (b) `help`: where the first word after it that is no flag is a name with a tool, that tool with `--help`; else the suite with the line as typed. (c) A first word that is a name with a tool: that tool with the rest. (d) Anything else, where there is a suite: the suite with the line as typed: every flag first (`--version`, `--json`, `-q`, `--no-color`, `-h`, `--help`, alone or with more), a word with no tool, a word that is no name.
- R3, with no suite. `--version` alone prints `agentik <VERSION> (no suite installed)`, exit 0. `help`, `-h` or `--help` alone print the list. A name with no tool exits 3 with R4's lines. Any other flag exits 2 with the usage line. A word that is no name exits 2 with `agentik: <word> is not a name: lowercase letters, digits and dashes`, then `next: agentik help`; the word is printed only when it is ASCII letters, digits, `.`, `_` and `-`, else the line starts `agentik: that word is not a name`.
- R4, not installed, exit 3, two lines on stderr: `agentik: <word> is not installed, and neither is the agentik suite`, then `next: git clone https://github.com/agentik-dev/agentik-commons && agentik-commons/setup`. The list ends with the same `next:` line on stderr and exits 0. The repo is `plan.SOURCE`'s; a test holds the two equal.
- R5, the usage line: `usage: agentik [<verb or tool> [args...]] | agentik help [<verb or tool>] | agentik --version`.
- R6, what stays. POSIX `sh`; reads and writes nothing, resolves no old name, prints no escape byte and no mark. `VERSION=0.3.0` in the pin's form. `prog.FLOOR` stays 0.2.0. The 100-line bound holds, the header comment giving way to GUIDE §10's row.
- R7, the files: the `may touch` row. No `scripts/sync`, no other repo.

The builder's reading where a ruling leaves a choice: with no suite, `help <word>` judges the word as R3 judges a first word (a name exits 3, no name exits 2) and `help` with a flag or two words prints the usage line; a word is a flag when it starts with `-`; the list reads PATH, then the door's own folder.

## 3. Acceptance

Each in a temp HOME; a tool and the suite are stubs that print their name and each argument in brackets.

| # | line | at the pin |
|---|---|---|
| 1 | suite on PATH: `--version`, `--version --json`, `--json`, `--no-color doctor`, `help --json`, `help doctor extra`, `--help --version`, `Config` each reach the suite unchanged, the door's exit the suite's | `agentik 0.2.0`; usage, exit 2 |
| 2 | the real suite behind the door: `--version` and `version` print one line, holding `plugin.json`'s version | two numbers |
| 3 | suite on PATH, no word: the suite with no argument; `help`, `-h`, `--help` reach it as typed | `[help]` for all four |
| 4 | a folder off PATH holds the door and a stub suite: the door by its path with `doctor` reaches it; a second suite on PATH wins | exit 3 |
| 5 | the same folder holds a stub tool: the door by its path reaches it, and `help <word>` with `--help` | exit 3 |
| 6 | no suite: a name with no tool exits 3 with R4's lines, stdout empty; the `next:` line under `sh -c` with a stub `git` and a stub `setup` exits 0 | one line, exit 127 |
| 7 | no suite: no word and `help` print the list, R4's `next:` on stderr, exit 0; `--version` R3's line; `--json` exit 2 with R5's line; `Config`, `a_b` exit 2 with R3's lines; an escape byte in a word is never printed | usage for the last three |
| 8 | a tool on PATH wins over the suite for its word, the arguments unchanged, an empty one included | holds |
| 9 | the two doors the same bytes; `sh -n`; R6's bound | holds |
| 10 | `scripts/door-probe` prints `door-probe: go` | go |
| 11 | the full suite under `/usr/bin/python3`; `make check` once, last, through the gate queue | |

## 4. Not built

The suite's refusals (sc4's), the first screen bare `agentik` now reaches (sc5), `agentik_install.py`, the launcher, each tool repo's copy of the door (`scripts/sync` in that tool's row), the suite's version (phase 2).
