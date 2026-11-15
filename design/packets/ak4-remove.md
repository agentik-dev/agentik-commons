# Packet ak4-remove: `agentik remove` takes a tool off the machine and says what it kept

| item | value |
|---|---|
| from | agentik-hq's brief ak4-remove of 2026-11-14, R1 to R9, acceptance 1 to 11; level S3 |
| pin | main at 182eab6 (suite 0.7.15, ak4b-uninstall landed); worktree `.claude/worktrees/ak4-remove`, branch `ak4-remove`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; `remove` runs only in a test's temp home, with stubs for `claude` and `ps`; made-up names; `agentik_install.py` not edited |
| may touch | `plugins/suite/lib/agentik_suite/remove.py` (new); `plugins/suite/lib/agentik_suite/cli.py` (the verb tables, `do_remove`); `plugins/suite/lib/agentik_suite/doctor.py` (`RESERVED`); `plugins/suite/lib/agentik_suite/messages.md` (`## Help`, a new `## Remove`); `tests/test_ak4_remove.py` (new); `tests/test_ak9c_plug_rest.py` (`test_4`); `tests/test_sc5_first_screen.py` (`PIN_KEPT`); the older tests that pin the verb list; `design/voice/checked.sha256`; `GUIDE.md` (§10); `NICE_TO_HAVE.md`; `history/NICE-overflow.md`; `plugins/suite/.claude-plugin/plugin.json`; this packet; `history/sittings/2026-11-14-17.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 11 below |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The owner's words and the design's

The owner, 2026-11-12: "how I configure my work computer with agentik plugins, and in general, how others might try out what I've written". The design:

> Remove is setup's plan reversed: `claude plugin uninstall`, then the launcher, its links and its frozen trees, by a new `uninstall` in the canonical install module. Config and state are listed and kept. With `--all` the plan ends with the marketplace (`claude plugin marketplace remove agentik`), the suite's own launcher and trees, the door and `~/.cache/agentik`, in that order, so "config and state only" is what `remove --all` leaves; what Claude Code keeps of its own is read from its files and listed, never guessed.

## 2. At the pin

Measured at 182eab6 in a temp HOME under `env -i`: `agentik-suite remove x --dry-run` prints `remove is not a verb or a tool` and `next: ... help`, exit 2; `remove` is in `doctor.RESERVED` and `cli.NEVER_MENDED`. hq measured `claude` 2.1.325: `plugin uninstall <id> --keep-data` keeps `plugins/data/<id>/` and `plugins/cache/agentik/<name>/<version>/`; `plugin marketplace remove agentik` empties its two entries and removes `plugins/marketplaces/agentik/`.

## 3. Rulings (the brief's, in short)

- R1: `remove PLUGIN...` or `remove --all`, with `--dry-run`, `--yes`, `--json`; neither, or both, is a usage error, exit 2, naming both forms; a name is checked as setup checks one. In `WRITES`, out of `doctor.RESERVED`; `--all` takes the key `remove_all`. `remove.py` calls `apply`, `plan`, `update`; `agentik_install.py` unedited.
- R2: the hold first (`update.hold`, `held remove: <what>`, exit 2, nothing written); then each tool's `uninstall(dry=True)`, any `kept: held` row holds the run before any `claude` command.
- R3: a tool is taken off where the finder's row is `own` at the user's scope, or the plugin is absent and `~/.local/bin/agentik-<name>` stands; any other kind is a `kept` row, no command, its launcher left. `--all`: every name the suite knows that meets this.
- R4: per tool, (1) `claude plugin uninstall <name>@agentik --keep-data` where installed; (2) `uninstall("agentik-<name>", spare=<this process and its parents>)`, its rows the plan's and the close's.
- R5: `--all`, after the tools: (3) `claude plugin marketplace remove agentik` where `known_marketplaces.json`'s entry names `agentik-dev/agentik-commons`, else `kept`; (4) `claude plugin uninstall suite@agentik --keep-data` where listed at the user's scope; (5) `uninstall("agentik-suite", door=True, spare=...)`; (6) `${XDG_CACHE_HOME:-~/.cache}/agentik`, a real folder at the cache home's real path plus `agentik`, the cache home neither `/` nor the home, by a walk that follows no link and checks each path is under it.
- R6: before step 5 every module, message and text the close needs is loaded; after it nothing is imported or read from the tree.
- R7: kept and listed, by `lstat`: `~/.config/agentik/<name>/`, the tool's `user_file`, its state folder and old-named one, `plugins/data/<name>@agentik/`, `plugins/cache/agentik/<name>/`; with `--all` the suite's config file and state folder.
- R8: setup's asking: one question on a terminal; off one without `--yes`, the plan and exit 2; off one with `--yes`, the `claude` steps refused where `apply.gated` names the settings file. A failed step stops, exit 1; `kept: partly removed` is exit 1; nothing to take off says so, exit 0. One `setup.jsonl` entry, `verb: "remove"`. `--json` is `agentik.remove/1`.
- R9: `## Remove` in `messages.md`; GUIDE §10; two NICE rows at S4; suite 0.7.16 alone, last under `plugins/`.

## 4. Interfaces

- `remove.do_remove(cmd, nouns)`; `remove.spare(pid)` returns this process and its parents' pids; `remove.cache_fate(env)` returns `(path, None)` to remove or `(path, why)` to keep.
- `agentik.remove/1`: `ok`, `held`, `dry_run`, `tools` (`name`, `plugin`, `rows`, each `{path, what, fate}`), `kept` (`{path, why}`), `ran`, `removed`, `wrote`; `steps` on a dry run, by `apply.step_json`.
- The journal entry: update's keys, `verb: "remove"`.

## 5. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `python3 -m unittest tests.test_ak4_remove -k test_1_` | red: no verb |
| 2 | `python3 -m unittest tests.test_ak4_remove -k test_2_` | the same |
| 3 | `python3 -m unittest tests.test_ak4_remove -k test_3_` | the same |
| 4 | `python3 -m unittest tests.test_ak4_remove -k test_4_` | the same |
| 5 | `python3 -m unittest tests.test_ak4_remove -k test_5_` | the same |
| 6 | `python3 -m unittest tests.test_ak4_remove -k test_6_` | the same |
| 7 | `python3 -m unittest tests.test_ak4_remove -k test_7_` | the same |
| 8 | `python3 -m unittest tests.test_ak4_remove -k test_8_` | the same |
| 9 | `python3 -m unittest tests.test_ak4_remove -k test_9_` | the same |
| 10 | `python3 -m unittest tests.test_ak4_remove -k test_10_` | the same |
| 11 | `python3 -m unittest tests.test_ak4_remove tests.test_sc5_first_screen tests.test_ak9c_plug_rest`; `make voice`, `make check`; `scripts/hygiene`, `scripts/hygiene --require-private --commits main..HEAD` | green but for the new file |

## 6. Choices

Listed in the charter's handover as they are made.
