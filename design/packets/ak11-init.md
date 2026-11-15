# Packet ak11-init: `agentik init --kind hq DIR` writes a fresh coordinating repo into an empty folder

| item | value |
|---|---|
| from | agentik-hq's brief ak11-init of 2026-11-13, R1 to R12, acceptance 1 to 22; level S3 |
| pin | main at dfa537f (suite 0.7.16, ak4-remove landed; su2 and in4 landed); worktree `.claude/worktrees/ak11-init`, branch `ak11-init`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; `init` runs only in a test's temp home; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/init.py` (new); `plugins/suite/lib/scaffold/hq/` (new, twelve files); `plugins/suite/lib/agentik_suite/cli.py` (R8's lines); `plugins/suite/lib/agentik_suite/messages.md` (`## Help`'s three runs, `flag.yes`, a new `## Init`); `tests/test_ak11_init.py` (new); `tests/test_agentik_suite.py` (a verb list only); `tests/test_sc5_first_screen.py` (`PIN_KEPT`); `.hygiene-allow` (two rows); `README.md` (one row); `design/voice/checked.sha256`; `NICE_TO_HAVE.md`; `history/NICE-overflow.md` (its oldest S4 row, moved by the byte bound); `plugins/suite/.claude-plugin/plugin.json`; this packet; `history/sittings/2026-11-15-1.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 22 below |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The owner's words

"The work computer is set up from the public repos alone, with a fresh hq scaffold." So `init` is the first verb he runs there after `setup`. Its texts are the design: the new repo's README, the first lines of each record, the last line `init` prints, copied byte for byte.

## 2. At the pin

Measured at dfa537f in a temp HOME under `env -i`: `agentik-suite init --kind hq X` prints `init is not a verb or a tool` and `next: ... help`, exit 2, and makes no folder (the brief's baseline at d795d4a read `init is not a verb. Run agentik-suite --help for the list.`; main has moved). `cli.py` ends its tables with `issue`; `VALUE_FLAGS` ends with `--draft`; the class ends with `do_issue`. `help install-cli` shows `--prefix` in the usage line alone, its rows `--dry-run` and `--yes`. `flag.yes` reads `Run setup's lines without asking first.`, pinned by no test. A tool's text passes through inline (`err.setup.step`'s `{last}`). `_walk` freezes dotfiles and skips `.DS_Store`. No shared call asks a person a question: `update` and `remove` each keep an `ask` of their own. `doctor.RESERVED` holds `init`; `test_sc5_first_screen.PIN_KEPT` pins every `verb.`, `usage.` and `flag.` id (39).

## 3. Rulings (the brief's, in short)

- R1: the packets before bind: the floor, `term` the one writer, the catalogue's voice, the streams, the `--json` object, the four exits, no tool's name in the package or its tests. New tests in `tests/test_ak11_init.py`.
- R2: `init --kind KIND DIR`, a write, with `--dry-run` and `-y`; it asks nothing; `KIND` is a folder under `plugins/suite/lib/scaffold/`, one today, `hq`; `init.py` holds `do_init(cmd, nouns)`.
- R3: the scaffold, twelve files, written once by the hq's script; from then on the repo's files are the source, held by a test: nine text files at their sha256, the record check byte-equal to `scripts/recordlint` with its sha256 line, `history/sittings/.gitkeep` empty.
- R4: the refusals, exit 2, one line, nothing written, in order: no or unknown kind; no DIR or a second word; no `git` on PATH; the parent no folder, or DIR no folder; a folder above holding `.git`; DIR holding more than `.git` and `.DS_Store` (`already` where its repo file reads `suite.kind` as the kind, else `not empty` naming three entries sorted, then `and N more`).
- R5: a stage beside DIR, mode 755; each file copied, 755 where it starts `#!`, else 644; `git init -q -b main` in the stage where DIR holds no `.git`, stdin closed, a 10 s wall; one rename, or each top entry renamed in; on an `OSError` or git's failure, exit 1, the stage and each moved entry removed. Nothing staged, nothing committed.
- R6: stdout the title, then each path, `README.md` first, then sorted; stderr one hint; DIR as typed; `--dry-run` the same list under its own title and hint.
- R7: `--json`: `agentik.init/1`, `ok`, `kind`, `dir` (absolute), `dry_run`, `git` (`made` or `kept`), `files`; a refusal's `error.code` one of `no_kind`, `bad_kind`, `no_dir`, `extra_word`, `no_git`, `no_parent`, `not_a_folder`, `inside_repo`, `already`, `not_empty`, `write_failed`, `git_failed`.
- R8: `cli.py`: `init` in the import, `"init"` last in `VERBS` and `WRITES`, `"--kind": ("kind", "init")` last in `VALUE_FLAGS`, `do_init` last in the class.
- R9: the catalogue: `verb.init`, `usage.init`, `flag.kind` at the end of their runs in `## Help`; the rest in a last section, `## Init`.
- R10: `.hygiene-allow`, two rows for the scaffold; `README.md`, one row of the verb table; a test that names the ledger's file assembles the name.
- R11: not this row's: `GUIDE.md`, `term.py`, `plan.py`, `fallback.json`, `scripts/recordlint`, `scripts/sync`; a NICE row says `sync` places no record check in a scaffolded repo.
- R12: one seam, `init._answers(cmd, nouns)`, returns `{"kind", "dir"}` or raises R4's refusals 1 and 2; it alone reads `cmd.opts["kind"]` and the nouns; it reads no stdin. A later row puts the suite's picker behind it.
- The start line (2026-11-15): commons is free, so the suite's version is bumped once, alone, in the last commit under `plugins/`.

## 4. Interfaces

- `init.do_init(cmd, nouns)`; `init._answers(cmd, nouns)` returns `{"kind": str, "dir": str}`; `init.kinds(lib)` the sorted kinds, each a folder under `init.scaffold(lib)`, the scaffold's folder.
- `agentik.init/1` as R7; on `git_failed` the error object holds `said`, git's stderr.

## 5. Acceptance

Lines 1 to 3, 5 to 18, 21 and 22 are the brief's, each a test of `tests/test_ak11_init.py` named `test_<n>_`; at the pin each is red (no verb, and line 21 at its import). Lines 4, 19 and 20 are run by hand and reported.

| # | line | at the pin |
|---|---|---|
| 1 | `python3 -m unittest tests.test_ak11_init -k test_1_` | red: no verb |
| 2 | `python3 -m unittest tests.test_ak11_init -k test_2_` | red: no verb |
| 3 | `python3 -m unittest tests.test_ak11_init -k test_3_` | red: no scaffold |
| 4 | by hand in a fresh hq: the ledger tool's `render --check`, then `render --lint` | not run |
| 5 | `python3 -m unittest tests.test_ak11_init -k test_5_` | red: no verb |
| 6 | `python3 -m unittest tests.test_ak11_init -k test_6_` | red: no verb |
| 7 | `python3 -m unittest tests.test_ak11_init -k test_7_` | red: no verb |
| 8 | `python3 -m unittest tests.test_ak11_init -k test_8_` | red: no verb |
| 9 | `python3 -m unittest tests.test_ak11_init -k test_9_` | red: no verb |
| 10 | `python3 -m unittest tests.test_ak11_init -k test_10_` | red: no verb |
| 11 | `python3 -m unittest tests.test_ak11_init -k test_11_` | red: no verb |
| 12 | `python3 -m unittest tests.test_ak11_init -k test_12_` | red: no verb |
| 13 | `python3 -m unittest tests.test_ak11_init -k test_13_` | red: no verb |
| 14 | `python3 -m unittest tests.test_ak11_init -k test_14_` | red: no verb |
| 15 | `python3 -m unittest tests.test_ak11_init -k test_15_` | red: no module |
| 16 | `python3 -m unittest tests.test_ak11_init -k test_16_` | red: no verb |
| 17 | `python3 -m unittest tests.test_ak11_init -k test_17_` | red: no verb |
| 18 | `python3 -m unittest tests.test_ak11_init -k test_18_` | red: no verb |
| 19 | `scripts/voice --catalogue plugins/suite/lib/scaffold/hq/README.md --sidecar <scratch>` | not run |
| 20 | `make voice`, `make check` through the gate; `scripts/hygiene`, `scripts/hygiene --require-private --commits main..HEAD` | green but for the new file |
| 21 | `python3 -m unittest tests.test_ak11_init -k test_21_` | red: no module |
| 22 | `python3 -m unittest tests.test_ak11_init -k test_22_` | red: no verb |

## 6. Choices

Listed in the charter's handover as they are made.
