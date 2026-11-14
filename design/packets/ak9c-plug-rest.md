# Packet ak9c-plug-rest: a claimed verb runs from `agentik <verb>`; two settings screens say what they read

| item | value |
|---|---|
| from | agentik-hq's brief ak9c-plug-rest of 2026-11-14, R1 to R9, acceptance 1 to 10; design/15 P2; level S3 |
| pin | main at 70dcd97 (suite 0.7.13, ak9b-plug-reader landed at 41c1822); worktree `.claude/worktrees/ak9c-plug-rest`, branch `ak9c-plug-rest`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; stubs in a temp HOME; made-up names; `sources.py`, `plan.py`, `term.py`, `fallback.json`, `GUIDE.md` and doctor's reads (ak9b R5 to R7) unchanged |
| may touch | `plugins/suite/lib/agentik_suite/cli.py` (`KEPT`, `_not_a_verb`, `_claimed`); `tools.py` (`claims`); `config.py` (the survey's claims, `_tool`, `_silent`, the warnings loop, `_card`'s `values` rows); `doctor.py` (`claims`, `twice`, `shadow`, `read`, `own_doctors`'s describes); `messages.md`; `plugins/suite/lib/kept.json`; `design/voice/checked.sha256`; `tests/test_ak9c_plug_rest.py`; `NICE_TO_HAVE.md`; `history/NICE-overflow.md`; `plugins/suite/.claude-plugin/plugin.json`; this packet; `history/sittings/2026-11-14-14.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 10 below |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The design's words (design/15)

> **P2, one owner.** A top-level verb is either the suite's or one tool's. [...] A tool's verb is a first-level verb of that tool, run as `agentik-<tool> <verb>` and claimed with `"top": true` in its `describe`; `agentik <verb>` then execs the tool. A verb two words deep under a tool (`agentik session gate land`) is not claimed and stays where it is. Two claims of one name: the suite runs neither, says which two, exits 2, and `doctor` fails.

> Reserved for a tool's claim under P2: `rows` (the decisions tool, design/16) and `guard` until design/20 names it.

The contract's words: a config read's warning is `{key, reason, value, path, line}`, `reason` one of `unknown`, `choice`, `unreadable` (key null: a file the tool skipped because it cannot parse it) and `ignored` (a key the tool knows and does not take from that file). A `values` row is `{layer, value}` and may also carry that layer's `path` and `line`, where a layer is several files.

## 2. Rulings (the brief's, in short)

- R1: `agentik W ...`, W first, no suite verb, reserved word, tool's name or plugin's name (all `_not_a_verb` settles first, unchanged): where one claim of W counts, the suite execs the claimant's file as `<file> W <later words unchanged>` by ak9b R1's path, printing nothing. A flag before W keeps the pin.
- R2: a claim is a `verbs` entry `{"name": W, "top": true}` of a describe that counts (ak9b R3). It counts where the standing source's kind is `own` and a file runs, W is no suite verb and none of `doctor`'s reserved words, and, where the suite keeps W for one tool (`KEPT`, beside `VERBS`: `rows` for `decisions`, `guard` for none), the claimant is that tool. The suite's own describe is no claim.
- R3: two claims that count: neither runs; one refusal naming the word and the tools, exit 2; `doctor` one FAIL row in the form of its shadow rows.
- R4: a claim that does not count is said under `config T`'s list (the word and why), never run; `--json` carries each claim as `{verb, counts, reason}`; `agentik W` refuses as at the pin, its `next:` `agentik T W` where exactly one tool claimed W without counting.
- R5: `rows` and `guard` join the words `doctor`'s shadow check reads.
- R6: the claims are read from the describes the cache holds, under `config`'s describe wall; a slow or uncounted describe claims nothing; a word that is nothing is refused inside that wall.
- R7: a warning `unreadable` reads as a file the tool skipped, with the file (and line), no key; `ignored` as a key the tool does not take from that file; `unknown`, `choice` and any other reason print the pin's bytes.
- R8: a card's `values` row with a `path` prints it after the value, its `line` where given, as the set-by line shows a file; none: the pin's bytes.
- R9: the messages and their sidecar; suite 0.7.14 alone in the last commit under `plugins/`; NICE rows after main's highest, one at S4 that `help` lists no claimed verb.

## 3. Interfaces

- `cli.KEPT = ("rows", "guard")`, also `Command.KEPT`; `tools.kept(lib, words)` reads each word's tool from `kept.json` beside the package (`{"rows": <the tool>}`), since no tool's name stands in the package (`test_agentik_suite`'s layout test), as `render.json` does; `Command._claimed(word)` reads the claims and runs one, refuses two, or gives R4's `next:`.
- `tools.claims(entries, described, kept_out, kept)` gives `[{tool, verb, counts, reason}]`, `reason` null, `suite`, `kept` or `market`; `doctor.claims(cmd, entries, described)` passes it `VERBS`, `RESERVED` and `KEPT`.
- `doctor.twice(cmd, claims)` gives R3's FAIL rows; `own_doctors(cmd, entries, described=None)` takes the describes `read` made.

## 4. At the pin

Measured at 70dcd97 by `tests/test_ak9c_plug_rest.py`, before the change: see the charter's Done-ness, act T.

## 5. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `python3 -m unittest tests.test_ak9c_plug_rest -k test_1_` (R1) | red, `ink is not a verb or a tool` |
| 2 | `-k test_2_` (R2, R4: another marketplace, a folder, a bare file on PATH) | red, no line |
| 3 | `-k test_3_` (R3) | red, no row |
| 4 | `-k test_4_` (R2's words, `rows` for `decisions`) | red, `rows is not a verb or a tool` |
| 5 | `-k test_5_` (R5) | red, no row |
| 6 | `-k test_6_` (R6: a hang, another name, no file) | green |
| 7 | `-k test_7_` (R7) | red, `unknown key None` |
| 8 | `-k test_8_` (R8) | red, not printed |
| 9 | bare `agentik`, `help`, `config`, `doctor`, `doctor --json` in a home with no claim against a `git archive` of the pin, the version aside | equal |
| 10 | `/usr/bin/python3 -m unittest discover -s tests`, the older files unedited; `make voice`, `make check`; `scripts/hygiene --require-private --commits main..HEAD` | green |

## 6. Choices

Listed in the charter's handover as they are made. Two meet the unedited tests: a claim's line is said on `config T` only where the finder knows a source for T (`test_agentik_suite` a1 and `test_sc4_errors` f7 hold a bare file on PATH whose `config T` has no line more on either stream), and the keeper's name is data (above).
