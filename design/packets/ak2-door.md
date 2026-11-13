# Packet ak2: the door falls through to the suite, and a probe over the door's writers

| item | value |
|---|---|
| from | agentik-hq's brief ak2 of 2026-11-13, R1 to R6; level S3 |
| pin | agentik-commons main 2ccedb1 (`Merge ak1b-config`, suite 0.3.0); worktree `.claude/worktrees/ak2-door`, branch `ak2-door`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no ledger; made-up names in fixtures; the probe's hand run clones into its own temp folder, runs `make` only with `-n`, builds nothing |
| may touch | `bin/agentik`; `plugins/suite/bin/agentik`; `plugins/suite/lib/agentik_suite/cli.py`; `plugins/suite/lib/agentik_suite/tools.py`; `plugins/suite/lib/agentik_suite/messages.md`; `plugins/suite/.claude-plugin/plugin.json`; `scripts/door-probe`; `tests/test_agentik.py`; `tests/test_agentik_suite.py` (`LayoutTest`); `tests/test_door.py`; `tests/test_suite_word.py`; `tests/test_door_probe.py`; `GUIDE.md` (§10); `README.md`; `design/voice/checked.sha256`; `.hygiene-allow`; `NICE_TO_HAVE.md`; this packet; `history/sittings/2026-11-13-5.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 8 below, each in a temp HOME; verify green |
| budget | a commit per ruling group by explicit path, this packet first, the version bump last; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"Make it a high quality modern CLI tool that is dynamic and has high quality concise human friendly feedback (using respeak to help with the voice)."

## 2. Rulings

The repo keeps no `DECISIONS.md`; the suite's management ledger binds it: hq entry 6 (`/usr/bin/python3` at a 3.9 floor, the standard library alone) and entry 37 (made-up names).

- R1, what stands: the packets ak1a and ak1b: the floor, `term` the one writer, `messages.md` and its voice (the result first, then the fact, then the next command), the grammar, the streams, the `--json` object, the four exits, no tool's name in the package, its messages or its tests. New tests go in new files. A new message goes under `## Errors`, directly after `err.verb`.
- R2, the door: `bin/agentik`, `VERSION=0.2.0`, `sh`, under 100 lines. `agentik <word> ...`: `agentik-<word>` on PATH is exec'd as today; else, with `agentik-suite` on PATH, `exec agentik-suite <word> ...`, the args unchanged; else exit 3 and one stderr line, `agentik: <word> is not installed here; agentik-commons/setup sets the suite up`. Bare `agentik`, `help`, `-h`, `--help` exec `agentik-suite help` where the suite is on PATH, else print today's list. `agentik help <word>`: `agentik-<word> --help`, else `agentik-suite help <word>`, else the exit 3 line. `--version`, a bad name's exit 2 and the head comment's account of the exits stay true. The door's lines are outside the catalogue.
- R3, a word the suite does not know: no verb, a plugin's name (the marketplace file's, a row of `fallback.json`, a `<name>@agentik` of `installed_plugins.json`), no `agentik-<word>` on PATH: exit 3, one line, it has no command here and `<tool> setup --dry-run <word>` shows the steps; `--json`: `ok` false, code `not_installed`. Any other word: exit 2 with the nearest of the verbs and those names. `help <word>` the same.
- R4, `plugins/suite/bin/agentik`: a `cp` of `bin/agentik`, held byte-equal by `LayoutTest`. No script places it.
- R5, the records: GUIDE §10's `front door` row says R2; its `exit codes` row says 3 as R2 and R3 have it, naming no repo. The old test in `tests/test_agentik.py` is rewritten for R2. The README's table gains the probe's row. No §11.
- R6, `scripts/door-probe [--code DIR] [--rounds N] [--keep]`, by hand, never by `make check`, in `suite-probe`'s shape: does each writer of the door leave a newer door in place? Under a temp folder it clones, at main, each git checkout in DIR (`--code`, else `AGENTIK_CODE`, else the folder above this repo's main checkout) holding a writer, found by shape; this checkout is left out. A launcher writer: `plugin/bin/agentik` and one executable `plugin/bin/agentik-*`, run as `<launcher> install-cli --prefix P`. Else a make writer: each line of `make -n install BINDIR=P/bin` whose last word is `P/bin/agentik`, run by `sh -c` in the clone, no other line. Each under `env -i`, a temp HOME, `PATH=/usr/bin:/bin`, a fresh P a case, a 20 s wall that kills its group. `kept` (this door plus a comment line, the same after) and `absent` (a door after, executable) give `ok` or `FAIL`; `fifo`, `raw` (a non-UTF-8 byte on `VERSION`, `LC_ALL=en_US.UTF-8`) and `race` (against a second clone at `VERSION=0.9.0`, over a `0.0.9` door, N rounds, default 20) give a `note`. One line a writer and case, the folder name first; last `door-probe: go` or `door-probe: stop: <n> failed`; exit 0, 1, 2. Nothing outside its temp folder, removed unless `--keep`.

## 3. Acceptance

Each in a temp HOME, every tool and plugin made up. At 2ccedb1 (measured): 1 prints `agentik: agentik-nosuch is not on PATH; it comes from agentik-dev/agentik-nosuch`, exit 3; 2 and 3 that line for `setup`, exit 3, bare `agentik` the list, `--version` `agentik 0.1.0`; 4 `pear is not a verb. Run agentik-suite --help for the list.`, exit 2, `paer` the same with no nearest; 5 no second door; 6 GUIDE names `agentik-dev/agentik-<tool>`; 7 no probe.

| # | line |
|---|---|
| 1 | no suite on PATH: `agentik nosuch`, `agentik help nosuch` exit 3, R2's line, one line, no `agentik-dev/` |
| 2 | a stub `agentik-suite` printing its args: `setup --dry-run` reaches it and its exit returns; bare, `help`, `-h`, `--help` give `help`; `help x` runs `agentik-x --help`, else the stub gets `help x`; `agentik x "a b" ""` runs `agentik-x`; `--version` `agentik 0.2.0`; `test_bad_names_exit_two` holds |
| 3 | `plugins/suite/bin` on PATH: `bin/agentik setup --dry-run` the suite's plan, exit 0; bare `bin/agentik` the suite's help |
| 4 | `pear` in a temp marketplace: `agentik-suite pear` exit 3, R3's line; `--json` one object, `ok` false, `not_installed`; `help pear` the same; `paer` exit 2 naming `pear`; a stub `agentik-pear` on PATH: `pear` exit 2 |
| 5 | the two doors byte-equal; `bin/agentik` passes `sh -n`, under 100 lines |
| 6 | GUIDE §10 holds R2's exit 3 line, no `agentik-dev/agentik-<tool>` |
| 7 | `tests/test_door_probe.py`: `suite-probe`'s three tests; `--code` at made-up checkouts, `--rounds 2`: a blind make writer `FAIL` at `kept`, `stop: 1 failed`, exit 1; a careful one alone `go`, exit 0; a launcher writer from this repo's `scripts/` `ok` at `kept` and `absent`. Then one hand run with no flag, its lines in the builder's record alone |
| 8 | `make check` green after `make voice` |

## 4. Not built

The suite's `install-cli`, the root `setup`, a `make install`, GUIDE §11, a tool's claimed top-level verb: the next row. Any change to `scripts/agentik_install.py`. A script that places the suite's copies; the 0.2.0 door in another repo. A lock across writers. Any install.

## 5. The landing

`plugins/suite/.claude-plugin/plugin.json` to `0.4.0`, alone in the last commit that touches `plugins/suite/`; nothing checks this bump. Fewer than ten new messages, so no respeak pass is owed.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, a relay ledger. The report: head sha, gate ids and exits, acceptance 1 to 8 at the pin and now; the probe's hand-run lines in the builder's record alone, since they name other checkouts.

## 7. Review 1's fix

Ruling: F1, F2 and F3 on the branch, each with a test red at 795ea2d; L5 rides; L1, L2, L4 and L7 are NICE n48 to n51; L3 and L6 stay with the review. The version stays 0.4.0 and its commit 4f332e4 stays where it is, so F3 and L5 touch `plugins/suite/` after it.
- F1 `door-probe` leaves out a checkout whose makefile holds a recipe line `make -n` runs: a `+` after any `@`, `-` or blank, or a `$(MAKE)` or `${MAKE}`, with one note for both
- F2 `door-probe` skips a folder in DIR it cannot read, with no Traceback
- F3 the suite's `--json` remedy for an unknown word names the nearest only when it is a verb, else `<tool> --help`
- L5 the door's head comment: the tool's or the suite's code wherever it execs one, bare and help included

## 8. Review 2's fix

Ruling: F1 again, a regression: matching `$(MAKE)` anywhere in a makefile left out the checkouts whose `$(MAKE)` sits in a comment, a value or another target's recipe. Now each makefile (`GNUmakefile`, `makefile`, `Makefile`, `*.mk`) is read into rules, and the scan counts only the recipe lines `install` reaches: its own rules and, through the prerequisites as written (order-only ones too), theirs. A checkout is left out with a note in two cases: a reached recipe line starts with `+` after any `@`, `-` or blank, or holds `$(MAKE)` or `${MAKE}`; or the reach cannot be read, because a reached target or prerequisite holds `$` or `%`, or a makefile has an `include`, `-include` or `sinclude` line. Its tests were red at 1d4d73c. NICE n52: build 2's first check, red on a timing test of ak1b's.
