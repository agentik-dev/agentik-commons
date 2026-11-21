# Packet sc12-picker: the picker as a component, with the yes or no selector and its probe

| item | value |
|---|---|
| from | agentik-hq's brief sc12-picker, amended 2026-11-21, on design/23 §4a and its Amendment 1 (§14); the owner's answer A to §10 question 1, the standard library alone; level S2 |
| pin | agentik-commons main b1894d8 (suite 0.7.40, `setup.ask.one` on it); worktree `.claude/worktrees/sc12-picker`, branch `sc12-picker`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test reads the live home or state; made-up names in fixtures and the probe; nothing that calls `pick` |
| may touch | `plugins/suite/lib/agentik_suite/pick.py`, `plugins/suite/lib/agentik_suite/term.py`, `plugins/suite/lib/agentik_suite/messages.md`, `design/voice/checked.sha256`, `plugins/suite/.claude-plugin/plugin.json` (the version), `scripts/pick-probe`, `tests/test_sc12_pick.py`, `tests/test_agentik_suite.py` (its `STDLIB` set gains `termios`, which R2 puts in `pick.py`), this packet, `history/sittings/*.md` |
| verify | `python3 -m unittest tests.test_sc12_pick` and the term tests directly; `scripts/pick-probe` on both Pythons by hand; `scripts/hygiene --require-private --commits main..HEAD`; `make check` once, last, through the gate queue |
| acceptance | 1 to 13 below |

## 1. The finding

The owner's words, 2026-11-13, on the picker: yes to a picker "like the one Claude Code has", with multiselect, select-one and tabbing between questions. After his first `./setup`: "Can you make the yes be a simple yes no selector that defaults to no? Typing yes wasn't intuitive. Also the prompt it gave is very confusing - it wasn't clear if I was suppose to type run. If you want me to do individual ones or all, maybe make it a multi selector. Not sure." On 2026-11-21 he ruled the library question: the standard library alone.

The base is the designer's prototype, which the refuter broke in three ways (design/23 §14.2): two ways out leave the terminal changed (Ctrl-\, a stopped screen), an escape sequence types into the text, and `same as:` does not give the pick back in three cases.

## 2. Rulings

- R1, the files: `pick.py` beside `term.py`; `term.put` (a write with no line break, and one that never waits) and `term.clean` widened to drop the zero-width characters; `term.columns` is the one column count. A `## Pick` section in `messages.md`, `scripts/pick-probe`, `tests/test_sc12_pick.py`. No caller.
- R2, the interface of 4a.2, and the one-reader test: `input(`, `stdin.readline` or `termios` in a file of the package but `pick.py` is red, but for four reads on named allow lines (`apply._before`, `issue._ask`, `remove.Remove.ask`, `update.Update.ask`), each left for a later row.
- R3, the screens of 4a.3, the marks, the ASCII marks, the plain prompt, `confirm`'s five states. R4, the keys of 4a.4, each escape form taken whole; a paste with no end closes after 1 s.
- R5, the terminal of 4a.5: `IXON` off; `TCSANOW`, input dropped, `tcflow(TCOON)`; no write that waits; SIGINT, SIGTERM, SIGHUP, SIGQUIT held and the first sent again; `leave()` modes first; SIGCONT retakes; a refused `tcsetattr` tried again; a terminal gone is a cancel.
- R6, 4a.6's two tables; `AGENTIK_PLAIN`; `termios` imported in the functions; a list longer than its window at the plain prompt reads a name.
- R7, `same as:` is `shlex.join(command(answers))`; `least` and the `other` check before any close. R8, `confirm`'s typed form reads one line as `apply._before` does. R9, under thirty messages. R10, the probe. R11, suite 0.7.41 alone in the last commit under `plugins/`.

## 3. Interfaces

- `pick.ask(t, questions, command)` gives `{id: answer}`; `pick.confirm(t, question, yes, no, typed, **values)` gives a bool; `pick.Other`, `pick.Cancelled`, `pick.NoTerminal`; `pick.layout(state, columns, rows)` gives `(lines, cursor)`, each line a list of `(text, sgr)` and the cursor `(line, column, shown)`; the states are `pick.State(t, questions, utf8)` and `pick.Confirm(t, question, yes, no, utf8)`; `pick.parse(buf, final, utf8)` gives one key.
- `Term.put(data, err=True, wait=True)`: with `wait` false the bytes go only as `select` says the stream takes them, 512 at a time, and what is left comes back.
- A question's `prompt` and `tab` and an option's `label` and `note` are text the caller gives; `prompt` is a message id filled by the caller's values (`values`).

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `scripts/pick-probe` exits 0 on `/usr/bin/python3` 3.9 and on a newer Python | no probe |
| 2 | `-k test_a2`: each key of 4a.4 gives its frame at 80 and 50; no line past its width; the frame keeps its height | the prototype's 43,200 frames held |
| 3 | `-k test_a3`: `ESC ESC [ A`, `ESC [ [ A`, OSC by BEL and by ST, DCS, an X10 report leave the filter empty | `[A`, `A`, `11;rgb:0000/0000/0000`, `1$rq`, ` !!` |
| 4 | probe `modes`: the modes after Enter, Esc, Ctrl-C, Ctrl-\, SIGTERM, SIGHUP, SIGQUIT and a raising `check` equal the ones before; the last bytes show the cursor, paste off | Ctrl-\ left `ICANON` and `ECHO` off |
| 5 | probe `stopped`: SIGTERM ends with 143 after Ctrl-S before, Ctrl-S during, 300 arrows unread | no exit until Ctrl-Q |
| 6 | probe `cont`: SIGSTOP, modes reset from outside, SIGCONT: a frame and a move; Ctrl-Z, SIGCONT: a frame, no traceback | not retaken |
| 7 | `-k test_a7`: `same as:` one quoted word, one command under `sh -c`; `Bad Name`, Up, Enter stays; `least` 1 stays and refuses `none` | two commands; answered; `same as: agentik setup` |
| 8 | probe `confirm`: Enter no, `y` Enter yes, `n` Enter no, `y` alone nothing, Esc and Ctrl-D no, one line each; an early Enter nothing | the typed line, Enter yes |
| 9 | probe `typed`: `TERM=dumb`, 30 columns, `AGENTIK_PLAIN=1`: one message, no escape byte, one line read | no typed form |
| 10 | `-k test_a10`: stdin a pipe, `CI=1` on a pty: `NoTerminal`, no byte | held |
| 11 | `-k test_a11`: `import pick` with `termios` hidden; `ask` gives the plain prompt | `import pick` fails |
| 12 | `-k test_a12`: the one-reader test red on a planted `input(` in `config.py` | no test |
| 13 | `scripts/hygiene --require-private --commits main..HEAD` exit 0; `make check` through the gate queue | green at b1894d8 |
