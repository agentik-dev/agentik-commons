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

## 7. The fix of review 1

Review 1 (an adversary, at 59c1069) found six things; the coordinator ruled F1 to F3 blocking and F4 to F6 riding, in one round on this branch, with four test gaps. The suite stays 0.7.16: the stamp commit is reverted and made again, alone and last under `plugins/`. `agentik_install.py` stays unedited.

- The cache folder (F1, F2). `<cache home>/agentik` is removed only where its real path is not, does not lie under and does not contain the config home and the state home (as the suite resolves them), Claude Code's folder (`CLAUDE_CONFIG_DIR`, else `~/.claude`) or any path R7 keeps; and is not and does not contain the home folder (lying under it is its place, `~/.cache/agentik`). R5's checks stand beside these. A relative or empty `XDG_CACHE_HOME` is ignored for `~/.cache`. Else `kept`, naming the path it would have reached.
- The close (F1). Each kept path is read again by `lstat`; one that is gone is a red row and exit 1.
- The door (F3). The plan's door row reads `would remove` where every entry that keeps it stands has a `would remove` row in the same plan.
- A hold mid-run (F4). Each tool's `uninstall(dry=True)` is read again right before its step 1: held with nothing yet done, it is R2's hold, exit 2; else the run stops, exit 1. Where step 2 still meets `kept: held` after step 1 ran, the run stops, exit 1, the journal's entry says exit 1, and the close names what holds and the line to run again once it ends.
- After step 5 (F5). A failed step 6 names the folder and says it is the person's to delete; the JSON remedy is null.
- The marketplace folder (F6). Listed as removed only where it stood before step 3 and an `lstat` finds it gone after; where it stands, a red row and exit 1.

| # | test (in `tests/test_ak4_remove.py`) | red at 59c1069, or under |
|---|---|---|
| F1 | `test_f1_a_cache_home_in_the_config_or_claudes_folder_is_kept`, `test_f1_a_kept_path_gone_is_red` | 59c1069 |
| F2 | `test_f2_a_home_named_agentik_under_the_cache_home_stays` | 59c1069 |
| F3 | `test_f3_the_door_the_run_removes_reads_would_remove` | 59c1069 |
| F4 | `test_f4_a_hold_that_starts_after_the_plan_stops` | 59c1069 |
| F5 | `test_f5_a_cache_walk_failed_after_the_door_names_the_folder` | 59c1069 |
| F6 | `test_f6_a_marketplace_folder_that_stands_is_red` | 59c1069 |
| gaps | `test_g_spare_with_a_ps_that_lists_the_caller` (spare returns `[]`), `test_g_a_failed_claude_step_stops` (a failed `claude` ignored), `test_g_a_tree_partly_removed_is_exit_1` (partly never stops), `test_g_steps_1_and_4_only_at_the_users_scope` (step 1 or step 4 at any scope) | their mutants |

| item | value |
|---|---|
| may touch | `plugins/suite/lib/agentik_suite/remove.py`; `plugins/suite/lib/agentik_suite/messages.md` (`## Remove`); `tests/test_ak4_remove.py`; `design/voice/checked.sha256`; `plugins/suite/.claude-plugin/plugin.json`; this packet; `history/sittings/2026-11-14-18.md` |
| leads not built | steps 3 and 4 against a real `claude`; the 32-ancestor spare |

## 8. The fix of review 2

Review 2 (an adversary, at 75ebb50) found five things; the coordinator ruled G1 and G2 blocking and started one hardening round on this branch for G4, a regression of the fix (a run that ended exit 0 ended exit 1), with G1, G2, G3 and G5 in it. The suite stays 0.7.16: the stamp commit is reverted and made again, alone and last under `plugins/`. `agentik_install.py` stays unedited.

- The settings files (G1). The cache walk's guard holds every catalogue tool's `user_file` (`fallback.json`), whether or not this run takes that tool off, and both `~/.claude` and `CLAUDE_CONFIG_DIR` where that is set.
- The suite's hold (G2). Under `--all`, where step 3 or 4 is to run, `uninstall("agentik-suite", door=True, dry=True)` is read again right before the first of them; a hold there stops the run as F4's rule says (nothing yet done: R2's hold, exit 2; else exit 1, the journal's exit 1, the line to run again).
- The bin and share folders (G4). The cache folder is also kept where it is, holds or lies under `<prefix>/bin` or `<prefix>/share`, the paths steps 2 and 5 act on. Where it is a row of step 2 or 5 (the door, say), step 6 gives it no row and the close no red check: the plan reads one fate for it, and the run ends exit 0.
- The close's words (G5). A path that was to go and still stands is closed by its own line (`err.remove.stands`), not by "what it said would stand does not".
- The guards' tests (G3). One test per guard term with the other terms out of reach, each red under its mutant: F2's home check (the XDG and Claude Code folders outside the home), the config home, Claude Code's folder, the "lies under" relation, and a relative `XDG_CACHE_HOME` used as given.

| # | test (in `tests/test_ak4_remove.py`) | red at 75ebb50, or under |
|---|---|---|
| G1 | `test_h1_every_settings_file_and_both_claude_folders_are_kept` | 75ebb50 |
| G2 | `test_h2_a_hold_on_the_suite_begun_mid_run_stops_before_step_3` | 75ebb50 |
| G4 | `test_h4_a_cache_home_in_the_bin_folder_gives_the_door_one_fate` | 75ebb50 |
| G5 | `test_f6_a_marketplace_folder_that_stands_is_red` (its line) | 75ebb50 |
| G3 | `test_h3_the_home_check_alone_keeps_a_home_named_agentik`, `test_h3_the_config_home_alone`, `test_h3_claude_codes_folder_alone`, `test_h3_a_relative_cache_home_is_not_used` | their mutants |

| item | value |
|---|---|
| may touch | `plugins/suite/lib/agentik_suite/remove.py`; `plugins/suite/lib/agentik_suite/messages.md` (`## Remove`); `tests/test_ak4_remove.py`; `tests/test_sc5_first_screen.py` (its pin, by the new id alone); `design/voice/checked.sha256`; `plugins/suite/.claude-plugin/plugin.json`; this packet; `history/sittings/2026-11-14-19.md` |
