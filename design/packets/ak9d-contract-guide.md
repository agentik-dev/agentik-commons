# Packet ak9d-contract-guide: the guide's §11, what a tool prints so the suite can read it

| item | value |
|---|---|
| from | agentik-hq's brief ak9d-contract-guide of 2026-11-14, R1 to R6, acceptance 1 to 8; level S3 |
| pin | main at e268e58 (suite 0.7.14, ak9c-plug-rest landed); worktree `.claude/worktrees/ak9d-contract-guide`, branch `ak9d-contract-guide`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; nothing under `plugins/` changes; no other line of `GUIDE.md` but §9's bullet; made-up names; the agentik-decisions checkout read only |
| may touch | `GUIDE.md` (a new §11, last; §9's bullet "A row's records are a folder"); `tests/test_guide_plug.py`; `.hygiene-allow`; `NICE_TO_HAVE.md`; this packet; `history/sittings/2026-11-14-15.md` |
| verify | `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 8 below |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. What it is for (the brief)

A tool joins `agentik config`, `agentik doctor` and `agentik status` by printing four kinds of JSON answer. What those answers hold was written once, for five builders, in a page outside this repo, and has parted from the reader in the places two later rows built. This row puts the contract in the guide every tool cites, as the reader reads it today, and adds the one test that keeps the two together.

## 2. Rulings (the brief's, in short)

- R1: `GUIDE.md` gains `## §11 The plug: what a tool prints so the suite can read it`, last, its seven parts numbered §11.1 to §11.7 (how the suite calls a tool; the envelope; `describe --json`; the config read; the doctor read; a status read; what every tool's tests hold), the page's four JSON examples each in a `json` fence, and its key tables.
- R2: every clause is held against the reader at the pin (`plugins/suite/lib/agentik_suite/`: `tools.py`, `config.py`, `doctor.py`, `status_read.py`, `cli.py`); where one contradicts the code, the clause says what the code does, and each mend is listed with its file and line in the hand-back. Where the suite reads nothing the page promised, the section says what a tool prints and stops. No rule the page and the code both lack.
- R3: the guide's voice: present tense, no "we", no date, history or suite version; no design record, row, brief, builder or `P<n>` label; a tool claims a word only for a first-level verb of its own that a person would type bare; the examples keep the made-up tool `demo`.
- R4: `tests/test_guide_plug.py`, stdlib `unittest`, cuts §11 out of the guide, takes its `json` fences in order and holds: four, each one object; the describe example counts by `tools.counted_describe`; the config example by `tools.counted_config`, three settings and one warning; the error example by `tools.config_error`; the doctor example by `doctor.read_answer`, one failed check. No private path, no process.
- R5: `.hygiene-allow` loses the two ak9c rows of `tests/test_ak9c_plug_rest.py` and `cli.py` and their comment; both scans exit 0. §9's bullet gains one sentence on who writes `done`: `agentik decisions rows close <row>`, held against agentik-decisions' `plugin/lib/decisions/rows.py`.
- R6: no other line of the guide; nothing under `plugins/`; where the reader looks wrong against the page, the section says what the code does and the difference is a `NICE_TO_HAVE.md` row at S4.

## 3. Interfaces

The reader's functions the test calls, as the reader calls them: `tools.counted_describe(code, out, name)` and `tools.counted_config(code, out)` with an exit and stdout bytes; `tools.config_error(out)` with stdout bytes; `doctor.read_answer(out, failed)` with stdout bytes and the detail of the fail check an `ok` false answer becomes. The test cuts §11 from its heading to the next `## ` line or the file's end.

## 4. At the pin

Measured at e268e58: `grep -c '^## §11 ' GUIDE.md` 0 (the guide ends at §10, 27,001 B); `grep -c 'rows close' GUIDE.md` 0; `.hygiene-allow` lines 34 and 35 are the two ak9c rows; `scripts/hygiene` and `scripts/hygiene --require-private --commits main..HEAD` exit 0; the check green as job 20261114-151338-1990.

## 5. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `grep -c '^## §11 ' GUIDE.md` is 1, and `§11.1` to `§11.7` each head one `### ` line | 0 |
| 2 | `python3 -m unittest tests.test_guide_plug`; with the describe example's `reads` made a string in a temp copy of the section, its describe test fails | no file; red on the missing section |
| 3 | every key of §11's tables is one the reader reads, or the section says the suite ignores it; the hand-back lists file and line for each key and each mend | the page's tables, held against none |
| 4 | §11 holds no `design/`, no row name, no `P<n>` label, no date and no `0.<n>.<n>` version | the page holds each |
| 5 | `.hygiene-allow` holds neither ak9c row; `scripts/hygiene` and `scripts/hygiene --require-private --commits main..HEAD` exit 0 | both rows stand, lines 34 and 35; both 0 |
| 6 | `grep -c 'rows close' GUIDE.md` is 1, inside §9's bullet | 0 |
| 7 | `git diff --stat main...HEAD` names `GUIDE.md`, this packet, the test, `.hygiene-allow`, `NICE_TO_HAVE.md` where R6 adds a row, and the charter alone | none |
| 8 | `make check` once, last, through the gate queue | green |

## 6. Choices

Listed in the charter's handover as they are made.
