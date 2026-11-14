# Packet rp6-verb: `issue`, the verb that joins scrub, gather, form and send

| item | value |
|---|---|
| from | agentik-hq's brief rp6 of 2026-11-13, R1 to R10 and amendments A1 to A6; hq design/22 §1, §3 items 1, 5, 6, 7, 10, 11, 14, 16 and the example, §7, §9; level S3; the sixth row of the suite's issue reporter |
| pin | main at aa8e16b (suite 0.6.12, rp2 to rp5 landed); worktree `.claude/worktrees/rp6-verb`, branch `rp6-verb`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test runs the real `gh`, `claude` or a tool, reaches the network or reads the real home; `issue send` only under a test's stubs; made-up names; no version (A6) |
| may touch | `plugins/suite/lib/agentik_suite/issue.py` (new), `cli.py`, `messages.md` (`## Issue` and the help lines), `scrub.py` (R10, below), `term.py` (`marked` and `keep`: term stays the one writer); `plugins/suite/skills/issue/SKILL.md` (new); `tests/test_rp6_issue.py`, `tests/fixtures/rp6-example.md` (new); `tests/test_rp5_send.py` (A2's reworded lines, and its R8 prefix test widened to the verb's ids); `README.md`; `.hygiene-allow` (the skill's row); `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-14-1.md` |
| verify | `make voice`, then `make check`, each once, last, through the gate queue, `--strict` |
| acceptance | 1 to 15 below; `python3 -m unittest tests.test_rp6_issue` OK |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The owner's words

"We should also have a way of reporting issues with agentik tooling that submits issues to github with relevant info to diagnose on this computer but with warnings and ways to remove identifying or private information. Issues should be concise, done via respeak, and approved by the user submitting the issue."

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names). The brief's R1 to R10 stand as written there; the amendments A1 to A6 are rulings. In short:

- R1 the frame, `term` the one writer, the catalogue, the streams, `--json` and the four exits bind; no tool's name in the package, its catalogue or the tests.
- R2 `cli.py`: `issue` in `VERBS` and `WRITES`; `ISSUE_FLAGS` (`--check`, `--web`, `--not-a-duplicate`); `--ran`, `--exit`, `--output`, `--expected`, `--as`, `--draft` value flags of `issue`; `do_issue` last.
- R3 the words: none (a read), `new [TOOL]`, `show`, `strike WORD...`, `drop SECTION...`, `edit`, `reword FILE`, `send`, `discard`; another word is exit 2 naming the nearest; a word but `new` takes the newest unsent draft or `--draft ID`; `--check` one line per unsent draft, exit 1 while one waits.
- R4 `new`: public table, machine, tool, facts (doctor `--json` in process), layer 1 then `bound`, the form, the draft folder (0700, `issue.md`, `draft.json`), the print of item 5; no network.
- R5 `strike`, `drop`, `edit`, `reword`: parse, `put`, `build`, one rename.
- R6 `send`: `--yes` exit 2 first; `sent.json` exit 1 with its URL; `lstat` of the folders and the file; one read; `check`, search, account, `approve`, `_file`; `--dry-run`, `--web`.
- R7 `discard`, `show`. R8 the skill. R9 the README part (no version, A6). R10 a module changes only where a signature does not meet a call.
- A1 after `bound`, `detect` each value; dirty is scrubbed and bound again; still dirty is `unreadable`; the same after `reword` and `edit`.
- A2 rp5's "send again" and "Run it from your own terminal" take the whole line by the slot `{send}`; `err.issue.send.as` names `--as LOGIN`. No `next:` line holds a character a shell reads.
- A3 a form still over its ceiling is written, its size and excess said, `drop` and `strike` named; `--json`'s `went` carries the pair.

### R10, the one line changed in a module

`scrub.scrub(text, m)` takes one optional argument, `state`, the numbering one draft shares, and `scrub.numbering(texts)` makes it, primed past the highest placeholder in `texts`: design/22 item 4 gives one value one placeholder for the whole draft, and a fresh state per value gave two values' different paths the one name `<path-1>`. With no `state`, today's behaviour.

## 3. Acceptance

Measured at aa8e16b: `agentik-suite issue` prints `issue is not a verb. Run agentik-suite --help for the list.`, exit 2; `plugins/suite/` holds no `skills` folder. The bound's caps are `gather`'s constants (`RAN`, `LINE`, `EXPECTED`, `ROW_DETAIL`) and the ceiling `form.CEILING`; the tests read them.

| # | line |
|---|---|
| 1 | bare `issue` in an empty HOME: exit 0, one line saying no draft waits, HOME unchanged; `issue --check`: exit 0 |
| 2 | the design's example, a stub doctor failing as it does: exit 0; `issue.md` equals `tests/fixtures/rp6-example.md` with its slots filled; the path's placeholder line named; `issue --check` exits 1 with one line |
| 3 | the same `new` with stdout piped: the draft's lines, joined, equal `issue.md`; no escape byte |
| 4 | `strike billing-api`: `Struck 1 word in 1 place: <struck-1>.`, one byte shorter, reads back; `strike details`, `strike 1`: 0 places, unchanged |
| 5 | `drop plugins output`: neither part, reads back; `drop nothing`: exit 2 |
| 6 | prose in `issue.md`: `send --dry-run` exit 1, kind `form`; a raw home path in its last lines: exit 1, the line and `path`, no byte of the path |
| 7 | in a pty, `send` typed: one search, one create whose title and stdin are the file; stdout the URL alone; `sent.json` holds it; a second send exit 1 with it, nothing recorded |
| 8 | `send --yes` exit 2, nothing read; from a pipe exit 2; `CLAUDECODE=1` exit 2; an open match exit 1 with its URL, `--not-a-duplicate` goes on to the screen |
| 9 | the drafts folder a link: `send` exit 2, nothing recorded |
| 10 | `reword` adding a capitalised name: exit 1, unchanged; a clean paraphrase: both values changed, the added words listed |
| 11 | a marker in the working folder's name, an environment value and the output file: in none of `issue.md`, `draft.json`, stdout, stderr |
| 12 | `new --json` R4's keys; `new nosuchtool` exit 2; `help` lists `issue`; `issue --help` its usage |
| 13 | `install-cli --prefix P`, then `P/bin/agentik-suite issue`: exit 0 |
| 14 | the skill holds the send line once, in the sentence that hands it over, in no fenced line; `scripts/plugin-description-bytes` passes |
| 15 | `make voice`, then `make check`, each once through the gate queue, green |

## 4. Not built

`new --render` (rp8); the guard rule (rp7); a seed from a finding; a label, a comment, a browser opened. The respeak pass over the new messages is the coordinator's. The version is phase 2's (A6).

## 5. The fix of review 1 and phase 2 (main at 9042a21, suite 0.7.0)

Main merged in; its rules run over the verb, and review 1's F1 to F6 and F8 are mended:

- sc4: every refusal of `issue` is a `Refusal`, its cause and then `next:` and the line typed, mended, where `cmd.offer` passes it. `offer` takes `issue.takes` (the refusals that read no file) and `issue.reads`: only bare `issue`, `--check` and `show` are offered, since no word but `send` keeps `--dry-run` and `send` is never offered; else `help issue`. send.py's refusals keep their words in the cause and name the help. sc2: each command comes from `cmd.say`; gh's own `auth switch` stays in the account's cause, as design/22 item 9 hands it over.
- F1: no cut lands before layer 1. gather keeps a free value whole (over 1 MiB it reads `unreadable` whole); a one-line window keeps its tail past its edge, its first 1,024 bytes and the word there dropped; the title's cut backs off a placeholder. A draft or render over the read cap is refused, not cut.
- F2: `reword` takes the words a render added after the layer. F3: `new` numbers past the given values and reports only the placeholders the scrub wrote. F4, F5: every word that acts on a draft checks the drafts folder and the draft as `send` did, and a file of the drafts that fails is a refusal that names no path. F6: each word answers `--json` with one object.
