# Packet ak4a-update: `agentik update` brings every installed tool and its command current in one call

| item | value |
|---|---|
| from | agentik-hq's brief ak4a-update of 2026-11-14, R1 to R10, acceptance 1 to 12; level S2 |
| pin | main at cab964a (suite 0.7.11, sc5-first-screen landed); worktree `.claude/worktrees/ak4a-update`, branch `ak4a-update`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; stubs for `claude`, `git`, `ps` and the session tool in a temp HOME; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/cli.py` (the verb table, `do_update`); `plugins/suite/lib/agentik_suite/update.py` (new); `doctor.py`'s `do_doctor` split into a read and its print; `apply.py`'s journal line (the verb); `messages.md` (`## Help`, a new `## Update`); `tests/test_ak4a_update.py`; the older tests that pin the verb list; `design/voice/checked.sha256`; `README.md`; `NICE_TO_HAVE.md`; `history/NICE-overflow.md`; `plugins/suite/.claude-plugin/plugin.json`; this packet; `history/sittings/2026-11-14-11.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 12 below |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The owner's words

2026-11-14, after updating a second computer by hand: "Why are there so many commands to run to do the updates? Can you make that easier to update?" Seven lines: the marketplace update, `claude plugin update` for a plugin, a listing of the plugin cache for the newest folder, its `install-cli`, a pull of the clone of this repo, its `plugins/suite/bin/agentik-suite install-cli`, the doctors.

## 2. At the pin

Measured at cab964a in a temp HOME under `env -i`: `agentik-suite update` prints `update is not a verb or a tool` and `next: ... help`, exit 2. The first screen is 9 lines with its hint. The launcher holds `VERSION` and `TREE` and nothing of the checkout it was frozen from.

## 3. Rulings (the brief's, in short)

- R1: `update [NAME...] [--dry-run] [--yes] [--json]`; in `VERBS` and `WRITES`; `help update` with the examples `update`, `update --dry-run`; the first screen keeps its 9 lines.
- R2: with no name, every name the suite knows (`tools.known`), `suite` included, that the finder gives a standing source; a name it does not know is `err.setup.name`. `own`: updated; `plugin` of the user's scope: updated from its marketplace; `folder`: `update.skip.folder`; undecided, a repo's scope or not found: setup's step 3 row, no command; `absent`: no row, and `hint.update.setup` where the name was typed.
- R3: the hold, first: a relay `run`, `gate` or `plan` in the process list (by the program's name, never a path's or a value's text), or a session tool's `unattended status --json` other than `null` inside 10 s; an unreadable list holds. `held install: {what}`, `hint.update.held`, exit 2, nothing run or written, `--dry-run` too.
- R4: the plan, five steps: marketplaces (`agentik` first), `claude plugin update T@M` (`suite` last), setup's step 4 rows, setup's step 5 rows, the doctor. `--dry-run` under `update.plan.dry`, exit 0; one question on a terminal; off one without `--yes`, the plan and `err.setup.yes`, exit 2; step 1 blocked, setup's row and exit.
- R5: steps 1 and 2 always run, through `apply.execute`; then the finder is read again and steps 3 and 4 come from `plan.build` on that read. A failure stops, exit 1, setup's failure lines; a second run converges. `update.tool.moved` or `update.tool.same` per tool.
- R6: `suite` standing (`own` or `plugin`): updated last, its command placed by that plugin's own `bin/agentik-suite install-cli`. Not standing: no fetch, pull or write; `update.suite.checkout`, then `hint.update.suite` where the marketplace's list names `suite`, else `hint.update.suite.pull`. `agentik_install.py` is not edited.
- R7: the doctor's read once after step 4, its rows and close under the update's; the exit is the update's. `update.nothing` where no version moved and no command was placed. The journal is setup's file, each line naming its verb.
- R8: `--json`, `agentik.update/1`: `ok`, `held`, `dry_run`, `tools`, `skipped`, `ran`, `wrote`, `doctor`; `steps` on a dry run, by `apply.step_json`.
- R9: hq measured that a plugin update moves `installed_plugins.json` and leaves Claude Code's user settings file's time alone, so `update` has no gate-list refusal: hq's measurement, not this row's.
- R10: `README.md` under 16,384 B (16,381 at the pin), `NICE_TO_HAVE.md` under 24,576 B (24,450 at the pin); suite 0.7.12 alone, the last commit under `plugins/`.

## 4. Interfaces

- `update.do_update(cmd, nouns)`; `update.hold(cmd)` returns `None` or the held text; `update.relay_pid(text)`; `update.SESSION_WALL = 10`.
- `doctor.read(cmd)` returns `(groups, failed, warned, total, entries)`; `do_doctor` prints it as at the pin.
- The journal entry gains `verb` (`setup` or `update`).

## 5. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `python3 -m unittest tests.test_ak4a_update -k test_1_` | exit 2, no verb |
| 2 | `python3 -m unittest tests.test_ak4a_update -k test_2_` | the same |
| 3 | `python3 -m unittest tests.test_ak4a_update -k test_3_` | the same |
| 4 | `python3 -m unittest tests.test_ak4a_update -k test_4_` | the same |
| 5 | `python3 -m unittest tests.test_ak4a_update -k test_5_` | the same |
| 6 | `python3 -m unittest tests.test_ak4a_update -k test_6_` | the same |
| 7 | `python3 -m unittest tests.test_ak4a_update -k test_7_` | the same |
| 8 | `python3 -m unittest tests.test_ak4a_update -k test_8_` | the same |
| 9 | `python3 -m unittest tests.test_ak4a_update -k test_9_` | the same |
| 10 | `python3 -m unittest tests.test_ak4a_update -k test_10_` | the same |
| 11 | `python3 -m unittest tests.test_ak4a_update -k test_11_` | the same |
| 12 | `python3 -m unittest tests.test_sc5_first_screen`; `/usr/bin/python3 -m unittest discover -s tests`; `make voice`, `make check`; `scripts/hygiene`, `scripts/hygiene --require-private --commits main..HEAD` | green |

## 6. Choices

Listed in the charter's handover as they are made.
