# Packet rm1-leave-clean: `remove --all` takes everything it wrote and leaves a way back

| item | value |
|---|---|
| from | the hq's brief rm1-leave-clean of 2026-11-16, R1 to R7; the install and upgrade review of that day, findings 9, 12 (the door's line), 13 (remove's kept list) and its lead on the order; level S3 |
| pin | agentik-commons main 93f0202 (suite 0.7.24, door 0.3.0); worktree `.claude/worktrees/rm1-leave-clean`, branch `rm1-leave-clean`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME with a stub `claude`; made-up names in fixtures |
| may touch | `scripts/agentik_install.py` `_launcher_form` and its copy `plugins/suite/lib/agentik_install.py`; `plugins/suite/lib/agentik_suite/remove.py` (`door_fate`, `kept`, `build`, `run`); `bin/agentik` and its copy `plugins/suite/bin/agentik` (the closing line, `VERSION`); `tests/test_rm1_leave_clean.py` (new); the cwd of `tests/test_door.py` and `tests/test_agentik.py` runs, and the door version they pin; GUIDE §10's front door row; this packet; the suite's version, alone, last |
| verify | `make voice` and `make check`, each through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` |
| acceptance | 1 to 6 below |

## 1. The owner's words

"Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

What the review met: with a session command written before the session tool's alpha.127, `remove --all` kept that launcher (`not the launcher install-cli wrote`), its links, tree, lock and share, and so kept the door; it took the suite, so no `remove` was left; the door's `next:` was the clone line, which fails where the clone already stands (`destination path 'agentik-commons' already exists`). The dry run gave the door's reason as `kept: agentik-agents stands`, an entry the run removes; the run said `agentik-session stands`. The kept list showed `~/.config/agentik/agents` twice. Not reproduced, a lead: step 3 removed the marketplace before step 4 uninstalled the suite's plugin.

## 2. Rulings

- R1, `_launcher_form` also takes the second line a session launcher carried before alpha.127, exactly as written (`` # agentik-session launcher, written by `agentik-session install-cli` (design/04 §2, §3); its old ``), for the name `agentik-session` alone. Everything else `_ours` tests stands; anything else not install-cli's is kept, as today.
- R2, the dry run's door reason names an entry that stays in the real run: the first, in sorted order, that no row of the plan removes. A test compares the dry run's rows with the run's, row by row.
- R3, the door's closing line where the suite is gone: `next: <path>/agentik-commons/setup` where `agentik-commons/setup` is an executable file in the cwd (or the cwd is a folder named `agentik-commons` holding one), by its full path where that path is plain, else as relative from the cwd; the clone line only where none is found. The door moves to 0.3.1 so a placed 0.3.0 door is replaced.
- R4, `remove --all` uninstalls each plugin, the suite's last, before the marketplace: the suite's plugin is step 3, the marketplace step 4. A second call after a cut finishes.
- R5, the kept list names each folder once (paths compared normalised), and names the suite's own plugin cache folder (`plugins/cache/agentik/suite`) where it stands; that folder gone after the run is no fault, since nothing named it before.
- R6, tests first, red at the pin; temp HOME, stub `claude` recording its arguments. No catalogue message changes; `make voice` through the gate.
- R7, other rows build in this repo now: only the functions named above change; the version 0.7.25 alone in the last commit.

## 3. Acceptance

| # | line | at the pin (93f0202) |
|---|---|---|
| 1 | `tests/test_rm1_leave_clean.py` `test_1`: suite at the worktree's version, a session command in the older form (made-up paths, two made-up links, a lock); `remove --all --dry-run` reads `would remove` on its launcher, links, share and the door, and `--yes` leaves nothing of agentik in `~/.local/bin` or `~/.local/share`; `LauncherForm` at the module | red: `launcher: kept: not the launcher install-cli wrote` |
| 2 | `test_2_every_plugin…`: the stub's record has each `plugin uninstall`, the suite's last, before `marketplace remove`, under a stub whose uninstall fails once the marketplace is gone; `test_2_a_second_call…`: a cut at the marketplace, then a second call finishes | red: `marketplace remove` before `uninstall suite@agentik` |
| 3 | `test_r2…`: a foreign `agentik-zz` stands; the dry run's door row is `kept: agentik-zz stands` and every row agrees with the run's; the door left by that run, in a folder holding the clone, prints `next: <path>/agentik-commons/setup`, which runs there and elsewhere; `DoorLine`: no clone, clone here, in the clone, a path with a space, a setup that cannot run | red: dry `kept: agentik-x stands`; the door prints the clone line |
| 4 | `test_r5…`: `~/.config/agentik/agents` once in `--json` and in the close; the suite's cache folder named; gone after the run, exit 0 | red: the folder twice; no cache row |
| 5 | `make voice` exits 0 through the gate | green (no message changes) |
| 6 | `make check` green through the gate; `scripts/hygiene --require-private --commits main..HEAD` exits 0 | green |

At the pin, 9 of the file's 13 tests are red; the 4 green hold today's behaviour (both module copies one, the clone line with no clone, a setup that cannot run, the suite's cache gone without fault).

## 4. Choices

- The door looks only in the cwd: the clone line itself runs in the cwd, so the cwd's clone is the one it collides with.
- An existing door test inherited the test process's cwd; it now runs in its temp HOME, so a run from a checkout named `agentik-commons` reads the same.
- The suite's cache row is listed only where it stands at the plan, and a gone one is dropped from the close, not marked red (the tools' own cache rows keep their red).

## 5. Not built

Claude Code's real behaviour on `marketplace remove` (no real `claude` was started); a clone found anywhere but the cwd; the other `next:` lines of finding 12.
