# Packet sc7-config-find: `agentik config <word>` searches every key

| item | value |
|---|---|
| from | hq design 23 section 4 (the paragraph "Finding a key without its tool"), section 3 (the command a line prints), section 8 (the voice rules); row sc6-config as built (its R6 cut, handed on); GUIDE section 9 (this shape) |
| pin | `main` at b703ad3 (suite 0.7.22); branch `sc7-config-find`, worktree `.claude/worktrees/sc7-config-find` |
| wall | this repo only; no push, `--amend`, rebase or merge; no install; no model started; the relay never run or built; one `make` at a time, through the gate queue; no tool's own `describe` output changed |
| may touch | `plugins/suite/lib/agentik_suite/config.py`, `plugins/suite/lib/agentik_suite/term.py` (the cut of a summary cell), `plugins/suite/lib/agentik_suite/messages.md` (the Config section), `design/voice/checked.sha256` (by `make voice`), `tests/test_sc7_config_find.py` (new), the tests that pin a line changed here, `plugins/suite/.claude-plugin/plugin.json` (the version, alone, last), this packet, the charter |
| acceptance | 1: in a temp HOME with two made-up tools, `loom` (the word in a key's segment) and `quill` (the word in a summary only), `config tension` lists both keys and no other, exit 0, and its `next:` runs under `sh -c`, the same on a pty and in a pipe (`tests/test_sc7_config_find.py -k test_a1`; pin: `FAIL  tension is not a tool here`, `next: config`, exit 2); 2: on this Mac `agentik-suite config turns` (the branch's launcher, from `/tmp`) lists `session.ceilings.turns` (pin: `FAIL  turns is not a tool here`, exit 2); 3: a summary past 80 columns is cut with `…` on a pty at 80 and prints whole in a pipe (`-k test_a3`; pin: no such screen); 4: `config loom` prints loom's screen as at the pin, and `config zzzq` the refusal with a `next:` that runs (`-k test_a4`; pin: the same, `next: config`); 5: `make voice` exits 0, `make check` green through the gate, `scripts/hygiene --require-private --commits main..HEAD` exits 0 |
| verify | `make check`, once, last, through the gate |

## Rulings

- R1, the search: a path whose first segment is no tool's name and that holds no dot is a search. Every tool that answers is read; a key matches where the word, case folded, is one of its dotted segments or a word of its summary. A tool's name always wins.
- R2, the screen: a title with the count and the word; one row a match, `tool.key`, value, summary, in `term.table`; on a terminal a summary that does not fit is cut with `…` (never a key, value, path or command); off one, one row a line, nothing cut. No card. `next:` names the first match's dotted path, the same on a pty and in a pipe. A tool that did not answer is one `!` line naming it.
- R3, no match: today's refusal (`… is not a tool here`), its `next:` naming the near tool, else the near key, where `difflib` finds one (`NEAR`).
- R4: a dotted path whose tool is unknown keeps today's refusal; no search runs on it.
- R5: messages in `messages.md` under Config, held to design 23 section 8; tests that pin a moved line move with it.
- R6: suite 0.7.23, alone in the last commit; the voice sidecar by `make voice` through the gate before it.

## Interfaces

- `term.cut(text)`: a cell `(text, "cut")`. On a terminal a cut cell that does not fit its room ends at it with `…`; a last cut cell with under 24 columns left goes under its row, cut to the width. Off a terminal it prints whole, unstyled.
- `config <word> --json`: `{"schema": "agentik.config/1", "ok": true, "word", "matches": [{"tool", "key", "value", "summary"}], "silent": [names]}`; no match is the refusal, as at the pin.

## Measure

A word of a summary is a run of letters, digits or `_` (`\w+`), case folded; a segment is the key split at its dots, case folded. Matches print in the order of `config`'s table of tools, each tool's keys in its own order. A tool that did not answer is step 1's marked row: a file that does not parse, a describe that failed or ran past 2 s, or a read that did.

## Choices inside the rulings

- The row carries no `*`: R2 names three cells, and the card the `next:` leads to says what is changed.
- No match: where a tool did not answer, its `!` line goes to stderr before the refusal, so the refusal is explained. The near key is the nearest segment of any key; the `next:` names the first key that holds it.
- The pin's exit for a refusal is 2 (the brief measured 0); a search that matches exits 0.
