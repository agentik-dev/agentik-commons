# Packet sc1-voice-sweep: the suite catalogue's messages to the voice rules, ids and placeholders kept

| item | value |
|---|---|
| from | hq design 23 section 8 (V1, V4, V6, V8, V10), section 9 (the row), section 14.2 (R1-F6); GUIDE section 9 (this shape) |
| pin | `main` at 8eeb8f5 (suite 0.7.20); branch `sc1-voice-sweep`, worktree `.claude/worktrees/sc1-voice-sweep` |
| wall | this repo only; no push, `--amend`, rebase or merge; no install; no model started; the relay never run or built; one `make` at a time, through the gate queue; the catalogue's message text and one test only, no module |
| may touch | `plugins/suite/lib/agentik_suite/messages.md`, `design/voice/checked.sha256` (by `make voice`), `design/voice/budgets.yaml` (a comment), `tests/test_sc1_voice_width.py` (new), the tests that assert a sentence changed here, `plugins/suite/.claude-plugin/plugin.json` (the version, alone, last), this packet, the charter |
| acceptance | 1: ids and placeholders unchanged, id by id (the verify-edit script of the respeak plugin, and a script of ours that prints the same two sets); 2: no message of R1 over 76 characters before its values (pin: 106 of the 139 rewritten were over; 136 of 747 over the whole catalogue, 47 more in the ids left); 3: none of R1 holds `this version`, `a later version` or `would` (pin: 10 of R1); 4: the ids left to other rows are byte for byte the pin's; 5: `make voice` exits 0, the sidecar committed, and `make check` green through the gate |
| verify | `make check`, once, last, through the gate |

## Rulings

- R1: a message outside the ids of R2 that broke V1 (76 characters before its values), V4, V6, V8 or V10 is rewritten; its id and each placeholder, by name and count, stay, and so does every number. 139 ids changed.
- R2: left, with the row that owns each: `setup.*`, `err.setup.*`, `hint.setup.*` (88, sc8); `doctor.*`, `hint.doctor.*` (66, sc10); `err.verb*` (8), `err.flag*` (3), `err.extra*` (2), `err.next` (1) (sc4, landed in the form of design/23 section 7); `install.done` (sc11); the Pick section (sc12, not in the catalogue yet). 169 ids, byte for byte the pin's.
- R3: `describe` stays in `usage.describe` and `err.describe.json`.
- R4: the scanner's budgets are four fixed keys (`respeak-measure.py`, `BUDGET_DEFAULTS`); it reads no width and no list of ids. The width is `tests/test_sc1_voice_width.py`, over every id but the ones R2 names and one prompt.
- R5: a test that asserts a sentence changed here changes in the same commit.
- R6: `make voice` through the gate, the sidecar committed.
- R7: suite 0.7.21, alone in the last commit.

## Measure

Width: the text after the id, backticks dropped, each placeholder counted as written (braces kept), which is longer than a value-free count; a message that fits so fits both ways.

## Choices inside the rulings

- `issue.render.contract` (291 characters) is the prompt the narrator model receives, and a test asserts its words: it is not printed to a person and stays as it is.
- Words that name the settings file (`verb.doctor`) read `the user file`, the name the other messages use for it.
- `Would place` and `would be an hq` (the dry runs of install and init) read `Plan: ...`, in the present, since V4 gives the exception to a title only and these are lines.
- `config.state.noread` keeps its sense with `keys`; design/23's `lists no keys yet` is its code row's.
- `usage.issue` lists the actions only, as `[new|show|...]`; their arguments are in `help issue`.
- Where a message gave a second sentence of advice and the width could not hold it, the cause and the one command stay; the advice dropped is the list `Mend that, then`, V2's own.
