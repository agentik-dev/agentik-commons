# Packet up3-forward-only: no step moves a command to an older version unasked

| item | value |
|---|---|
| from | the hq's brief up3-forward-only of 2026-11-16, R1 to R5; the install and upgrade review of that day, finding 5; level S3 |
| pin | agentik-commons main 17f4ed5 (suite 0.7.29); worktree `.claude/worktrees/up3-forward-only`, branch `up3-forward-only`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME with a stub `claude`; made-up names in fixtures |
| may touch | `scripts/agentik_install.py` (`install`, `install_cli`, `_behind`, a new `newer` and `_ahead`) and its copy `plugins/suite/lib/agentik_install.py`; `plugins/suite/lib/agentik_suite/install.py` (`do_install_cli`); `cli.py` (an `INSTALL_FLAGS` row for `--force`); `plan.py` step 4; `doctor.py` (`plan_rows`, a `NOTE` map); `messages.md` (`setup.launcher.newer`, `doctor.plan.newer`, `install.newer`, `flag.force`); `tests/test_up3_forward_only.py` (new); this packet; the suite's version, alone, last |
| verify | `make voice` and `make check`, each through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` |
| acceptance | 1 to 5 below |

## 1. The owner's words

"Use up to 2 Fable agents to review our upgrade/install so far. Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

What the review met: an older plugin's `install-cli` placed its version over a newer command (`/session:install-cli` from a session started before an update, the remedy every launcher's `is gone` line names); the suite's own did the same, 0.6.13 over 0.7.24. With the command at 1.9.3 and the plugin at 1.9.0, the doctor read `at 1.9.3, older than 1.9.0` and `update --yes` ran the 1.9.0 plugin's `install-cli`. The door and SessionStart's refresh held: both move forward only.

## 2. Rulings

- R1, `install()` in the module and the suite's copy: where the command in place is one install-cli wrote (`_ours`: its form, `TREE` under the share), its code stands (the runner in its `TREE`) and its version is newer than the tree being placed, nothing is written; the result holds `kept`, the newer version, and `install_cli` prints one line with both versions and returns 0. `force=True` places anyway. The comparison is `newer(a, b)`, the one `_behind` (refresh's) now calls; no second.
- R2, the suite's `install-cli` goes through the same `install()`; it takes `--force`, prints `install.newer` and `--json` gains `kept` where it leaves one, and is as at the pin where it places.
- R3, plan step 4, a launcher of the agentik marketplace's own plugin (`kind` own) newer than it by `newer`: `ok`, `setup.launcher.newer`, no command. `update` builds its rows from step 4, so it runs no older `install-cli` over it.
- R4, the doctor maps that row to `doctor.plan.newer` with the status `note`; `doctor.plan.behind` (`older than`) stays only on `setup.launcher.behind`, which a newer launcher no longer reads.
- R5, session's own `install()` and the sync to the tools are not this row.
- Tests first, red at the pin; temp HOME, stub `claude`. New messages hold design/23 §8; `make voice` through the gate.

## 3. Acceptance

| # | line | at the pin (17f4ed5) |
|---|---|---|
| 1 | `ToolTest`: a made-up plugin's 1.9.0 `install-cli` over its 2.0.0 command leaves 2.0.0, one line names both and `--force`; with `--force` it places 1.9.0; the dry run returns `kept`. `SuiteTest`: the suite's `install-cli` over a command at 9.0.0 leaves it, one line, `--json` `kept`; `--force` places | red: 1.9.0 placed; `--force is not a flag of install-cli` |
| 2 | `PlanTest`: launcher 1.9.3, plugin 1.9.0: step 4 `ok` `setup.launcher.newer`; the doctor's row a note that says newer; `update --yes` and `setup --yes` leave 1.9.3 and run no `install-cli` | red: `todo` `setup.launcher.behind`; `warn`; 1.9.0 placed |
| 3 | an older, equal, gone-code or foreign command is placed by `install-cli`; an older one by `setup --yes` and `update --yes`; the doctor still says `older than` for an older one; `--force` is install-cli's alone; the suite's copy is byte-equal | green (9 tests hold today's behaviour) |
| 4 | `make voice` exits 0 through the gate | green |
| 5 | `make check` green through the gate; `scripts/hygiene --require-private --commits main..HEAD` exits 0 | green |

At the pin, 9 of the file's 18 tests are red.

## 4. Choices

- A newer command whose code is gone is placed: leaving it would leave a command that cannot run, and its `is gone` line names this `install-cli`.
- Only an own-kind launcher reads `newer` in step 4: a declared other source's version is placed on purpose (`setup.launcher.other`), as at the pin. A version neither side of `order` reads stays `behind`, as at the pin.
- Step 5's own comparison (`setup.suite.newer`) is left as it stands; the doctor's suite row is not turned into a note.
- A tool's own command line passes `force` to `install_cli` only once its verb takes `--force`; that is each tool's row, after the sync.
- The kept line prints alone: no door, prune or PATH line, since nothing was written.

## 5. Not built

Session's own `install()` (another row); each tool's `--force` word on its `install-cli` verb; the sync of the module to the tools.
