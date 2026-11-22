# Packet sc15-setup-pick: setup's yes or no as a selector that rests on no, and `setup --pick`

| item | value |
|---|---|
| from | agentik-hq's brief sc15-setup-pick, amended 2026-11-21, on design/23 4a.2, 4a.3, 4a.6, 4a.7, §5 and §14; level S2 |
| pin | agentik-commons main 205dbce (suite 0.7.41, `pick.py` as sc12 landed it); worktree `.claude/worktrees/sc15-setup-pick`, branch `sc15-setup-pick`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test reads the live home or state; made-up names in fixtures; `pick.py`, `issue.py`, `remove.py` and `update.py` unchanged |
| may touch | `plugins/suite/lib/agentik_suite/apply.py`, `plugins/suite/lib/agentik_suite/cli.py`, `plugins/suite/lib/agentik_suite/messages.md`, `design/voice/checked.sha256`, `plugins/suite/.claude-plugin/plugin.json` (the version), `tests/test_sc15_setup_pick.py`, `tests/test_sc12_pick.py` (its allow list), `tests/test_sm1_setup_ask.py` and `tests/test_ak3_setup.py` (an answer sent once the question shows), this packet, `history/sittings/*.md`; build 2 (review 1): `tests/test_sc5_first_screen.py` (its pin), `tests/test_up1_tree_gone.py` (its pty helper), `.hygiene-allow`, `NICE_TO_HAVE.md`, `history/NICE-overflow.md` |
| verify | `python3 -m unittest tests.test_sc15_setup_pick tests.test_sm1_setup_ask tests.test_ak3_setup tests.test_sc12_pick` on `/usr/bin/python3`; `scripts/doclint`; `scripts/hygiene --require-private --commits main..HEAD`; `make voice` and `make check` once, last, through the gate queue |
| acceptance | 1 to 11 below |

## 1. The finding

The owner, after his first `./setup`, where he typed `yes` at "Run each `run:` line above, and the lines the later steps need? Answer y or n." and two commands ran: "Can you make the yes be a simple yes no selector that defaults to no? Typing yes wasn't intuitive. Also the prompt it gave is very confusing - it wasn't clear if I was suppose to type run. If you want me to do individual ones or all, maybe make it a multi selector. Not sure."

At the pin setup asks sm1's typed question on any pty, `CI` set or not, and reads one line in `apply._before`, the last read outside `pick.py` that sc12's allow list names for this file. `--pick` is refused as no flag of setup.

## 2. Rulings

- R1, the question: `apply._before` asks through `pick.confirm` with the typed form's ids `setup.ask` and `setup.ask.one`; new messages `setup.confirm`, `setup.confirm.one`, `setup.confirm.yes` (`Run them`), `setup.confirm.yes.one` (`Run it`), `setup.confirm.no` (`Don't run anything`). A test holds each question the first sentence of its typed message. The count stays `apply.planned`.
- R2, where each form shows: design/23 4a.6's second table, by `pick`'s own reading; `_before` also reads `CI` set to a value as off a terminal (new: at the pin `CI=1` on a pty asked and ran). On setup's path alone (review 1 F1): `_terminal`, which `remove` and `update` share, reads as at the pin.
- R3, the answers: Enter alone, `n`, Esc, Ctrl-D and Ctrl-C are a no, with the pin's lines and exit 2; `y` or the up arrow, then Enter, a yes; `--yes` asks nothing.
- R4: a no on a terminal after a bare run (no name, no `--pick`) prints `other plugins: <setup> --pick` before the pin's lines for a no; it is no `next:` line.
- R5, `setup --pick`: one `many` through `pick.ask` before the plan, `least` 1, an `other` row checked by the name rule of `err.setup.name`; the options, their notes and their order as in section 3. Its answer builds the plan as the same names on the command line do. Esc and Ctrl-C are a no as R3; `NoTerminal` and `--json` plan as with no `--pick`.
- R6: the one-reader test's allow list loses `apply.py`'s line.
- R7: `help setup` gains a `--pick` row and an `AGENTIK_PLAIN=1` row; `make voice` green, the sidecar committed.
- R8: suite 0.7.42, alone in the last commit under `plugins/`.

## 3. Interfaces

- `apply.pick_names(cmd, nouns) -> names`: the `--pick` question. Options: each name of the agentik marketplace the suite reads with no network that `plan.known` knows (review 1 F2: no row setup refuses), the default set first in the manifest's order, then the rest by name; the suite itself left out. Measured at the pin: a clone holds the marketplace's `.claude-plugin/marketplace.json` three folders over the package's `lib` (names and descriptions) and `lib/public.json` (names); a frozen tree holds `public.json` alone; a machine where the marketplace is known adds its `installLocation`'s file. Note: the description, `installed; ` before it where `installed_plugins.json` names `<name>@agentik`. Ticked: the names given, else the default set. `command`: the hint's words for `setup` (a `~/` word given as its full path, so the joined line runs as pasted), then `--dry-run` and `--yes` where given, then the names in the list's order.
- `cli.PICK_FLAGS`, `--pick` for setup alone; another verb refuses it as no flag of its own.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `-k test_a1`: pty 80x24, the four-line frame, Enter runs nothing, exit 2, HOME unchanged | typed question; Enter exit 2, ran 0 |
| 2 | `-k test_a2`: `y` Enter and Up Enter each run the plan; count asked = commands run, plans of one and several | `y` exit 0 |
| 3 | `-k test_a3`: `n` Enter, Esc, Ctrl-D, Ctrl-C run nothing; the modes after equal before | `n`, Ctrl-D, Ctrl-C exit 2 |
| 4 | `-k test_a4`: the typed question's bytes under `TERM=dumb`, 30 columns, `AGENTIK_PLAIN=1` equal the pin's; `y`, `YES`, `n`, `run`, Enter as at the pin | `Run these 3 commands now? y for yes, n or Enter for no.`; y, YES exit 0; n, run, Enter exit 2 |
| 5 | `-k test_a5`: `--yes`, a closed and a piped stdin as at the pin; `CI=1` on a pty the refusal for no terminal | closed, pipe exit 2 `cannot ask you here`; `--yes` exit 0; `CI=1` asked, ran |
| 6 | `-k test_a6`: `--pick --dry-run`, empty HOME, focus to `relay`, space, Enter: `same as:` ends `setup --dry-run session decisions agents relay`; the plan equals that line's in a pipe | `--pick is not a flag of setup`, exit 2 |
| 7 | `-k test_a7`: no tick, Enter stays and says why; `Bad Name` on `other`, Up, Enter stays and names the cause | the same refusal |
| 8 | `-k test_a8`: `--pick </dev/null` as `setup </dev/null`, no byte read; `--pick --yes --dry-run </dev/null` plans the default set | the same refusal |
| 9 | `-k test_a9`: bare no on a pty prints `other plugins:`; a named run and runs off a terminal do not | no such line |
| 10 | `tests.test_sc12_pick`: the allow list names no `apply.py` | four reads, `apply.py` one |
| 11 | `make check` green through the gate queue | green at the pin's landing |

## 5. Findings that name this row

- `cmd.say("setup")` from a clone's `setup` is the typed path alone, with no `setup` word, so `command` splits the whole hint line for its answers rather than a prefix (found by the clone's own probe, now `test_a6_from_the_clone`).
- `pick.ask`'s `same as:` is `shlex.join` of the argv, which would quote a `~/` word; `command` gives that word as its full path, so the line runs as pasted. Not a defect of `pick.py`: an argv holds no `~`.
- Commit eac3d56 named two tools in five asserts of `tests/test_sc15_setup_pick.py` (hygiene's `sibling` group); a76ba71 reads them from the plugin, and the history keeps the hit.
- The typed form drops a `y` typed before the question shows, where at 0.7.41 it was a yes: the design's 4a.2, and it stands (review 1's observation).
- Review 1 F1: `CI` in the shared `apply._terminal` made `remove` and `update` refuse under `CI=1` on a pty where the pin asked; build 2 reads `CI` in `_before` alone. F2: a name only a clone's marketplace file holds was offered and then refused; the list now offers only `plan.known`'s names.
- The first check's two reds: sc5's pin of the kept message ids gains `flag.pick` (55; without it main's 54 and hash), and up1's pty harness typed its `y` ahead, which the question now drops; it shares ak3's helper, `test_ak3_setup.on_pty`.
