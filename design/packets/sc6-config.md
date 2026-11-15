# Packet sc6-config: `config` in three steps, each ending on a command that runs

| item | value |
|---|---|
| from | hq design 23 section 4 (steps 1 to 3, up to the search by a bare word), section 3 (the command a line prints), section 8 (the voice rules), section 9 (the row), section 16 (sc5 as built); GUIDE section 9 (this shape) |
| pin | `main` at f697db9 (suite 0.7.21); branch `sc6-config`, worktree `.claude/worktrees/sc6-config` |
| wall | this repo only; no push, `--amend`, rebase or merge; no install; no model started; the relay never run or built; one `make` at a time, through the gate queue; no tool's own `describe` output changed |
| may touch | `plugins/suite/lib/agentik_suite/config.py`, `plugins/suite/lib/agentik_suite/cli.py` (the `--all` flag of `config`), `plugins/suite/lib/agentik_suite/messages.md` (the Config section and `flag.config_all`), `design/voice/checked.sha256` (by `make voice`), `tests/test_sc6_config.py` (new), the tests that pin a line changed here, `plugins/suite/.claude-plugin/plugin.json` (the version, alone, last), this packet, the charter |
| acceptance | 1: a made-up tool of 24 keys prints at most 20 lines at step 2 on a pty at 80 columns and all 24 flat in a pipe (`tests/test_sc6_config.py -k test_a1`; pin: 35 lines on the pty, a heading for each of 9 first segments in the pipe); 2: a changed key shows its `path:line` at steps 2 and 3 (`-k test_a2`; pin: step 3 only, step 2 shows none of 4); 3: each `next:` of steps 1 and 2 runs as printed, exit 0, the same on a pty and in a pipe (`-k test_a3`; pin: the same on both, but neither runs: `config TOOL lists one tool's keys.`, `config loom.KEY shows ...`); 4: `config loom ink.weight` and `config loom.ink.weight` print the same bytes (`-k test_a4`; pin: the same, sc4 R5); 5: `make voice` exits 0, `make check` green through the gate, `scripts/hygiene --require-private --commits main..HEAD` exits 0 |
| verify | `make check`, once, last, through the gate |

## Rulings

- R1: the words after `config` are one path joined by dots before anything is read (built at sc4 R5, kept); every line printed writes the dotted form.
- R2, step 1: the title `Keys by tool: C of T changed from their defaults.`; one row a tool: its name, `N keys  M changed` (the two counts aligned down the rows), `lists no keys yet` or `did not answer`, then its user file; `!` only on a row that did not answer or whose source is undecided; `next:` names the tool with the most changed keys, the first in the table's order on a tie. No `from a list:` line (sc14).
- R3, step 2: the title with the count, `(*)` when one is changed, and the layers lowest first; the changed keys first, `*`, key, value, layer, `path:line`; then, past 20 keys on a terminal, one line a group (its name, its count, its keys after the dot, `*` on a changed one); at 20 or fewer one flat table in the same columns; off a terminal or with `--all`, every key flat, one a line. A prefix (`config loom.weave`) prints that group flat. An unknown key in a file is a `!` line with its `path:line`. `next:` names the first changed key, else the first key.
- R4, step 3: `tool.key = value  (default D)`, the summary, then `set in`, `layers`, `choices`, `change`, `applies`. No `next:`. Nothing written.
- R5, `path:line`: see Measure.
- R6: a summary cut with `…` in `term.table` (see Choices).
- R7: every line in `messages.md` under Config; the tests that pin a moved line move in the same commit.
- R8: left: the search by a bare word (sc7), `--pick` (sc14), every tool's own `describe` output.
- R9: suite 0.7.22, alone in the last commit; the voice sidecar by `make voice` through the gate before it.

## Interfaces

- `config --all`: a flag of `config`, its own key `config_all` (as remove's `--all`), so `help config` glosses it and doctor's gloss stays. At step 1 and step 3 it changes nothing.
- `--json` of every step is the pin's, byte for byte: the screens change, the objects do not.

## Measure

`path:line` (R5): the line is the tool's own where its answer gives `source.line`. Where it gives a path and no line, the suite reads that file in the strict subset (`settings.read`) and takes the line of the key's dotted path, and for the `repo` and `local` layers, whose file holds a section a tool, of `<tool>.<key>` first; a file that does not parse, is absent, or holds no such path gives the path alone. The `change` row's `edit <path>:<line>` takes the line of the block's last key in that file, found the same way; where the block's key is not in the file yet, the path alone. The suite's own keys carry their lines from its parser, every layer.

Lines are counted as printed: a pty's output split at newlines, its escape bytes dropped. A key row in a pipe starts `*` or a space.

## Choices inside the rulings

- A group is the keys that share a first segment, or a dotted key alone; the keys with no dot that share it with none go on one row, `the rest`, after the groups.
- The flat forms list each key once: the changed ones first, then the rest in the tool's order.
- The step-2 table shows `path:line` for every key not at its default layer, changed or not; a key at its default shows no path.
- The title's layers are those present or named by a key's value, lowest first, as the tool orders them.
- At step 1 a tool whose describe fails, times out, or whose read fails is `did not answer`, its reason in the next cell where the pin gave one; a tool that answers and names no read, or ships no command, `lists no keys yet`, with its file from the suite's table.
- R6: no screen of this row puts a summary in a table cell (the card prints it on its own line), so `term.table` cuts nothing and is unchanged; the cut waits for the first table that holds a summary.
- The source card (`config suite.sources.X`) keeps the pin's lines; only the key card is R4's.
