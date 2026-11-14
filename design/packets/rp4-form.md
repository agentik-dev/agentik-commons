# Packet rp4-form: `form.py`, the issue's form written and read back byte for byte

| item | value |
|---|---|
| from | agentik-hq's brief rp4 of 2026-11-13, R1 to R6; hq design/22 §3 items 6, 7, 10, 11 and the example under item 16, §9 (R1-F4, R1-F9, R1-F11, R1-F12); level S3 |
| pin | agentik-commons rp1-shapes 23330e2 (reviewed, waiting in the landing queue); worktree `.claude/worktrees/rp4-form`, branch `rp4-form`; nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; made-up names; no module of rp2, rp3 or rp5 imported |
| may touch | `plugins/suite/lib/agentik_suite/form.py`; `tests/test_rp4_form.py`; `tests/fixtures/rp4_form_example.md`; this packet; `history/sittings/2026-11-13-21.md` |
| verify | `make check`, once, last, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_rp4_form` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"Issues should be concise, done via respeak, and approved by the user submitting the issue." Concise is the form's job: a title, four labelled lines and a folded diagnosis, under 4 KB. Three builders work beside this row from the same pin (`scrub`, `gather`, `send`); this row touches only its own files.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names).

- R1, what stands. One new module, `form.py`, and its tests. It prints nothing, holds no catalogue id, imports `hashlib` and `re` alone, names no tool (a tool is a value; a test's tool is made up) and imports no module of the rows beside it.
- R2, a draft's fields, one dict for the writer and the reader: `tool`, `title`, `ran`, `exit`, `happened`, `expected`, `versions` [item], `system` [item], `counts` [failed, warned, passed], `rows` [[tool, status, name, detail]], `plugins` [item], `others`, `lines` [text], `version`, `fingerprint`. Free: `title`, `ran`, `happened`, `expected`, each row's `name` and `detail`, each of `lines`; every other value typed, each with a pattern the reader enforces. A dropped section is None: `rows` (checks), `plugins`, `system`, `ran` with `lines` (output), `expected` (words).
- R3, the form, schema `agentik-issue/1`: the first line `<tool> <title>`, a blank, then `**Ran:**`, `**Happened:**`, `**Expected:**`, `**Versions:**`, a `<details>` fold (summary `Diagnosis: <f> failed, <w> warned, <p> passed`, the table `tool | status | check | detail`, `Plugins: <items>, and <n> other`, `Last lines:` in a fence) and the marker `agentik-issue/1 <tool> <version> <fingerprint>`; one line break at the end. Every free value outside the fence is a code span of its own, one backtick longer than any run it holds, padded where it opens or closes with a backtick; a `|` in a cell is `\|`; the fence is three backticks or one more than the longest run in the lines. The labels are constants. A dropped section's lines are absent; the fold is absent when the table, the plugins and the lines all are; an empty free value is a fixed word outside a span.
- R4, the signatures, called as written by the join and `send`: `build(fields) -> bytes` (a single-line free value with a line break is a `ValueError`); `parse(data, tools) -> fields`, raising `NotTheForm` with its 1-based line, strict: `build(parse(d)) == d` or it raises; `free(fields) -> [(key, line, value)]` in the form's order; `put(fields, key, value) -> fields`; `draft(facts, tool, title, happened, fingerprint) -> fields` from an `agentik.issue-facts/1` object; `subject(tool, ran, exit, rows, launchers)` and `fingerprint(tool, subject) -> 12 hex` (`ran:<tool>:<verb>:<exit>`, `ran:other:<exit>`, or `check:<tool>:<name>:<eight words>`; SHA-256 of `agentik-issue/1 <tool> <subject>`); `fit(fields, ceiling=4096) -> (fields, went)` (plugins, then `warn` rows, then the oldest lines); `nothing_new(render, fields) -> [miss]` and `added(render, fields) -> [word]`.
- R5, the title is plain text, 72 bytes for the line, cut on a character's edge; a title that opens with the verb the caller gives does not say it twice.
- R6, not this row's: `cli.py`, `messages.md`, `.hygiene-allow`, `README.md`, `plugin.json`, any other test file.

## 3. Acceptance

Measured at 23330e2: `form.py`, its tests and `tests/fixtures/` do not exist. The designer's prototype wrote the design's example as 801 bytes and read it back; by the first draft's rule a strike of the form's words broke a marker line, and 22 checks of a live doctor read gave 15 fingerprints.

| # | line |
|---|---|
| 1 | `build` of the design's example, its tool a made-up name of the same length, equals `tests/fixtures/rp4_form_example.md`, 801 bytes, written once and read by eye |
| 2 | `parse(build(f), tools) == f` and `build(parse(d, tools)) == d` for 200 seeded field sets whose free values hold backtick runs of one to five, pipes, `</details>`, `<summary>`, an `@name`, `#12`, a line of three backticks, letters outside ASCII |
| 3 | each of the five sections dropped, alone and all at once: none of its lines in the bytes, and they read back |
| 4 | `NotTheForm` with its line for: prose; a reworded label; a row's tool outside `tools`; a marker's tool unlike the title's; a fence closed early by a shorter run; a value outside its span; a second marker; text after the last line |
| 5 | `free(f)` lists each free value once, in order, each `line` the line `build` holds it on; `put` then `build` changes that value and no other byte |
| 6 | `fingerprint("alpha", "ran:alpha:doctor:2")` is `71c680c682c0`; the subjects and fingerprints `c46cab703536` and `276969ee989b` of the brief |
| 7 | two rows of one tool named alike, details unlike: two fingerprints; one command with two flags: one; a capitalised or digit word after the verb: not in the subject |
| 8 | `fit`: 9 KB comes back under 4,096 bytes, plugins first, then `warn` rows, then the oldest lines, `went` naming each; a set under the ceiling comes back unchanged |
| 9 | twelve planted renders: two pass; seven planted words, a dropped placeholder and dropped error text each miss; a lowercase paraphrase of a path passes and `added` lists its words |
| 10 | a 200-byte title with a four-byte letter at the cut: a line of 72 bytes or fewer, valid UTF-8 |
| 11 | `make check`, once through the gate queue, green |

## 4. Not built

The scrub of a free value and `strike` (rp2). What `send` refuses (rp5), which calls `parse`, `build` and `free`. The drafts folder, `drop`, `edit`, `reword` and the render's call (rp6, rp8).

## 5. The landing

`plugin.json` stays as it is: rp6 takes the version. Phase 2 merges main after rp1-shapes lands.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, a relay ledger. The report: head sha, the gate's id and exit, acceptance 1 to 11 at the pin and now.
