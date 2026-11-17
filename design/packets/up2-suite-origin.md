# Packet up2-suite-origin: a clone install is upgraded by one exact line that `update` prints

| item | value |
|---|---|
| from | agentik-hq's brief up2-suite-origin of 2026-11-16, R1 to R7; level S3; the install and upgrade review's findings 3 and 4 |
| pin | agentik-commons main 93f0202 (suite 0.7.24); worktree `.claude/worktrees/up2-suite-origin`, branch `up2-suite-origin`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME, a temp prefix and a stub `claude`; no network |
| may touch | `scripts/agentik_install.py` and its copy `plugins/suite/lib/agentik_install.py` (`launcher_text`, `_locked_install`, `install`, `read_launcher`, a new helper beside them), `plugins/suite/lib/agentik_suite/update.py` (`tail`, `hints`, the close's table, `skipped_json`, `_run`'s close), `messages.md`'s `update.suite.*` and `hint.update.suite*`, `README.md` (its top, its maintainers' part), the tests named below, `design/voice/checked.sha256`, `plugins/suite/.claude-plugin/plugin.json`'s version, this packet, `history/sittings/*.md` |
| verify | `make voice` and `make check`, each through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` |

## 1. The owner's words

"Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

The review (finding 3): on a clone install `agentik update` moves every tool and leaves the suite's own command where it was, its row marked `ok`, its `next:` a sentence and not a command. (Finding 4): the README's top has an install line and no upgrade line, and its maintainers' part calls the two `claude plugin` lines an update, which leave every command behind.

## 2. Rulings

- R1, `install-cli` run from a checkout (its plugin at `<checkout>/plugins/<name>`, the checkout holding `.git` and an executable `setup`, and not under Claude Code's plugins folder) writes `CHECKOUT=<path>` on the line after `TREE=`; from a plugin's folder it writes none. Run from a frozen tree it keeps the line the launcher it replaces holds, where that checkout still stands. A path with a control character or `=` gets no line, so `_ours`' one-`TREE=`-one-`VERSION=` count holds. `read_launcher` gives `checkout`, None where absent. `_launcher_form` is unchanged: the second line is the same in both forms.
- R2, in `update`, the suite placed from a checkout is step 4's row as a `note` (state `todo`, no command), never `ok`. Where the launcher names its checkout the row names it, and the close ends on a reason line and then `next: git -C <path> pull --ff-only && <path>/setup` alone (the path quoted for sh, `~` for HOME); where it names none the row says so and the `next:` is `claude plugin install suite@agentik` alone, its reason above, whether or not the marketplace lists `suite` (review 1 F2; `hint.update.suite.pull` is gone). Where it names a path that no longer reads as a checkout (the folder gone, or its `.git`), the row names the path and says so (`update.suite.checkout.gone`), and the close is the plugin's line as above (review 1 F1). The suite's lines are the close's last.
- R3, the close's table row for the suite plugin that did not move speaks of the plugin: `the suite plugin <version>, already current`.
- R4, the README's top gains the upgrade line inside the ten-line form; the maintainers' part no longer calls the two `claude plugin` lines an update.
- R5, setup's close (`apply.py`'s report) is not this row's.
- R6, tests first, red at the pin, in temp HOMEs with a stub `claude`; each message added holds design/23 §8 and the width test; `make voice` through the gate.
- R7, the version `0.7.25` alone in the last commit.

## 3. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `tests/test_up2_suite_origin.py`: from a made-up checkout, `install-cli` writes `CHECKOUT=`; from a plugin's folder, none; from the frozen tree, kept; a path with `=`, none; `read_launcher`, `_launcher_form` and `_ours` read both forms; uninstall's dry run takes either | no `CHECKOUT` line; `read_launcher` has no `checkout` key |
| 2 | a suite launcher naming its checkout: `update --yes` shows step 4 as `note` naming the path, and the close's last two lines are the reason and `next: git -C <path> pull --ff-only && <path>/setup` | `4  ok  agentik-suite  agentik-suite 0.7.24 was placed from a checkout, so update leaves it.`; `next: to have … update cover it too: claude plugin install suite@agentik`, then the doctor's own `next:` last |
| 3 | no line in the launcher: the note says the checkout is not named; `next: claude plugin install suite@agentik` alone | as above |
| 3a | review 1: a named checkout whose folder or `.git` is gone: the note names the path, "no longer a checkout"; no line, listed or not: the reason, then `next: claude plugin install suite@agentik`; no "pull that checkout" (tests 14 to 16) | at 8d9f653: `came from a checkout its command does not name`; unlisted, `next: pull that checkout, …` |
| 4 | end to end: a made-up clone of a local bare repo; its `setup --yes` places the suite; `update --yes` prints the line; the line run as printed by `sh -c` pulls the clone forward and starts its setup; no network | no line printed |
| 5 | a suite plugin already current: the close's row reads `the suite plugin 0.2.0, already current` | `ok  suite 0.2.0, already current` |
| 6 | a launcher written at the pin (no line): update, doctor and `remove --all --dry-run` read it as before (the existing suites, unchanged, green) | green |
| 7 | `scripts/readme-top` passes with the upgrade line; the maintainers' part holds no `Updates stay` | 8 lines, in the form; no upgrade line |
| 8 | `make voice` exit 0; `make check` green through the gate; hygiene over `main..HEAD` exit 0 | green |

## 4. Not built

Setup's close naming `agentik update` (up4, after ic1). The doctor's own `next:` still prints where it has one, above the suite's lines. `update.nothing` ("everything is current") beside a suite left behind is up1's line.
