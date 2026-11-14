# Packet ak9b-plug-reader: a plugin's word runs, a failed settings read says why, the doctor names each failing check

| item | value |
|---|---|
| from | agentik-hq's brief ak9b-plug-reader of 2026-11-14, R1 to R10, acceptance 1 to 10, and the start line's fh13 lead and NICE row; level S3 |
| pin | main at b99f677 (suite 0.7.12, ak4a-update landed); worktree `.claude/worktrees/ak9b-plug-reader`, branch `ak9b-plug-reader`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; stubs in a temp HOME; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/cli.py` (`_not_a_verb`); `tools.py` (`counted_describe`, `describe_all`, the config error, the one-line cleaning); `config.py` (the survey, `_list`, `_silent`, the key line); `doctor.py` (`read_answer`, `own_doctors`, `_rows`, `close_command`, `screen`); `status_read.py` (the one `counted_describe` call); `messages.md`; `plugins/suite/lib/fallback.json`; `tests/test_ak9b_plug_reader.py`; the older tests that pin a doctor's starts or the fallback rows; `design/voice/checked.sha256`; `README.md`; `NICE_TO_HAVE.md`; `history/NICE-overflow.md`; `plugins/suite/.claude-plugin/plugin.json`; this packet; `history/sittings/2026-11-14-12.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 12 below |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The finding

Each tool answers `describe --json`, a config read, and a doctor read (`agentik.doctor/1`: `ok`, `failed`, `warned`, `checks` of `{name, status, detail, remedy}`, a status one of `ok`, `note`, `warn`, `fail`). At the pin: a plugin whose command sits under its own root, off PATH, is refused (`is a plugin with no command`, exit 3) while the finder says that file runs; a config read that answers `"ok": false` with an `error` reads as `unreadable`, its reason and remedy lost; the doctor asks every tool `doctor --json` whatever its describe names, and closes a failing tool's group on that tool's own doctor, which shows the same failure again; a command that answers `describe` under another tool's name is counted as that tool's.

## 2. Rulings (the brief's, in short)

- R1: a first argument that is no verb and names a known tool whose finder row says a file runs: the suite replaces itself with that file (`os.execve`), every later argument unchanged, the same streams, the environment the launcher restored; nothing printed. The fh13 lead: a tool with a `page` whose file at `~/.local/bin/agentik-T`, off PATH, is the finder's run.
- R2: no file runs, or the row is `undecided`: the pin's refusal, byte for byte; a file passed over never runs; a suite flag before the word keeps the pin's handling.
- R3: `counted_describe(code, out, name)` counts an answer only when its `tool` is `name`; else the state is `unreadable` with `reason` `other` (`config.reason.other`) or, for an answer that does not read, `unread` (`config.reason.unread`), beside the state on every config screen and under `reason` in `--json`.
- R4: a config read's `"ok": false` object with string `code` and `message` and a string or null `remedy`, whatever the exit, is a counted error: `config.read.error`, `config.state.read_error` with `hint.config.remedy`, `err.config.read.error`; `--json` `"read": "error"` and `"error"`; the message one line, at most 300 characters, no control byte.
- R5: the doctor reads each tool's describe first (cache, wall); a counted answer naming a `doctor` read runs that read's `argv`, under the doctor's deadline and bound; it counts when one object, schema `agentik.doctor/N`, N at most 1, `ok` true (an `ok` false keeps sc10's one fail check) and the checks of the contract's shape; the exit is not read.
- R6: a counted answer's rows: each `fail`, then each `warn`, in the tool's order, with sc10's `fix:` line; then `doctor.tool.checks` or `doctor.tool.check` for the rest, notes counted; a detail cleaned as R4's message.
- R7: `failed` and `warned` over every check; a failing counted group whose fails name no remedy the close may run closes on `hint.doctor.fail.plain` with `cmd.say("doctor")`.
- R8: no counted describe or no doctor read: the pin's two rounds and rows; a read past the deadline, unstartable, over the bound or not counting: the pin's `doctor.tool.slow` and `doctor.tool.unreadable` rows.
- R9: `fallback.json`'s row with empty `lines` leaves. R10: suite 0.7.13 alone, the last commit under `plugins/`.

## 3. Interfaces

- `tools.counted_describe(code, out, name)`; `tools.describe_reason(code, out, name)` gives `None`, `other` or `unread`; `tools.describe_all(..., reasons=None)` fills `{name: reason}`.
- `tools.config_error(out)` gives `{code, message, remedy}` or `None`; `tools.one_line(text)` is R4's cleaning.
- `doctor.read_answer(out, failed)` takes schema N at most 1; `doctor.PLAIN` is the close that names no command of its own.

## 4. At the pin

Measured at b99f677 by `tests/test_ak9b_plug_reader.py`, before the change: lines 1, 3, 4, 5, 6, 8 and the lead red; 2, 7, 9 green; `fallback.json` five rows.

## 5. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `python3 -m unittest tests.test_ak9b_plug_reader -k test_1_` (R1, hD) | red, exit 3 |
| 2 | `-k test_2_` (R2, hB, a flag first) | green |
| 3 | `-k test_3_` (R3, hK) | red, counted as T's |
| 4 | `-k test_4_` (R4, hD) | red, `unreadable` |
| 5 | `-k test_5_` (R5, R6) | red, the text run's row |
| 6 | `-k test_6_` (R7) | red, no plain close |
| 7 | `-k test_7_` (R8) | green |
| 8 | `-k test_8_` (R4, R6 cleaning) | red |
| 9 | `-k test_9_` (R8, the text run) | green |
| 10 | `-k test_10_` (R9) and `/usr/bin/python3 -m unittest discover -s tests` | five rows |
| 11 | `-k test_11_` (the fh13 lead) | red, `has no command here yet`, exit 3 |
| 12 | `-k test_12_` (update's close rows are doctor's); `make voice`, `make check`; `scripts/hygiene --require-private --commits main..HEAD` | not measured |

## 6. Choices

Listed in the charter's handover as they are made.

## 7. The fix of review 1

The coordinator's ruling of 2026-11-14 on review 1's finding F1 and its leads, built in one round, each line with a test red at 40df089:

- F1 (S2, a regression of sc10's screen): R6's rows and order, R7's plain close and the 300-character cut reach only the answer of R5's doctor read. A tool whose describe names no doctor read, or that answers no describe, keeps the pin's rows, order, close and `--json`, byte for byte: round 1's `doctor --json` is read by the pin's `read_answer`, and R5's read by `read_own`. sc10's a3 and r1f2 end on the pin's close again.
- Lead 1, ruled as sc5's R8: R4's config remedy goes behind `next:` only where it holds neither `--yes`, `-y` nor the word `remove`. One that does is printed on its own line as the tool wrote it, cleaned (`config.remedy`), and the close names the read (`hint.config.again`, `cmd.say("config", T)`).
- Lead 2: a remedy that holds a control byte or a newline is no remedy (`tools.plain`), for R4's close and `--json`, and for a check of R5's read, its `fix:` line and the close it feeds.
- R3 (lead 4): a `tool` that is no string takes the reason `unread`. R5 (lead 7): a doctor read whose `argv` is empty does not count, so the tool gets the pin's two rounds.
- The wall (lead 3): R5 reads describe first, so the worst case is the describe wall and the doctor's deadline; the module's docstring says so.
- Stand as built: an `ok` false answer of R5's read in sc10's form (lead 6); R1; R9; suite 0.7.13.
- To NICE at S4 (leads 3, 5, 8, 9, 11): the config table's settings column where a reason shows; the two timing tests' patched wall; `help T` against `T --help`; a describe summary's size in `config --json`; R3's reason on the doctor's screen.

| # | line | at 40df089 |
|---|---|---|
| 9 | `-k test_9_` (F1: the pin's screen and `--json` of sc10's path, as bytes taken at b99f677) | red |
| 13 | `-k test_13_` (lead 1) | red, `next:` and the remedy |
| 14 | `-k test_14_` (lead 2: config and doctor) | red, the second line joins |
| 15 | `-k test_15_` (R3) | red, `other` |
| 16 | `-k test_16_` (R5) | red, the tool run bare |
