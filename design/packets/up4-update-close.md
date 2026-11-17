# Packet up4-update-close: update's close says what it did and what is left

| item | value |
|---|---|
| from | agentik-hq's brief up4-update-close of 2026-11-16, R1 to R6; level S3; the install and upgrade review's findings 6, 7, 11, 12, 13 and 15 |
| pin | agentik-commons main 17f4ed5 (suite 0.7.29); worktree `.claude/worktrees/up4-update-close`, branch `up4-update-close`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME, a temp prefix and a stub `claude`; no network |
| may touch | `plugins/suite/lib/agentik_suite/update.py` (`scope`, `detail`, `tail`, `hints`, `held`, `execute`, `_run`, helpers beside them), `messages.md`'s `update.*`, `hint.update.*` and `err.update.*` rows, `tests/test_up4_update_close.py`, `tests/test_ak4a_update.py` (tests 16 and 19, which read the old `next:`), `design/voice/checked.sha256`, `NICE_TO_HAVE.md` (one row) and `history/NICE-overflow.md` (n170 and n171 moved there by the byte bound), `plugins/suite/.claude-plugin/plugin.json`'s version, this packet, `history/sittings/*.md` |
| not touched | `plan.py`, `apply.py`, `doctor.py`, `remove.py`, `install()`, setup's messages; the suite's row and its two hints (up2) |
| verify | `make voice` and `make check`, each through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` |

## 1. The owner's words

"Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

## 2. Rulings

- R1 (finding 7), where a plugin moved, the close has one line: sessions started before this keep the old plugins until they are restarted. On a stop too, where step 2 moved one before it.
- R2 (finding 6), where step 2 moves the plugin of a tool whose table row holds a `page`, its close row is a `note`, never `ok`: the plugin moved, its command is at `<path>` (the file the finder names) and stays as it was, and under it the page's line. Where no file runs, the row says the command is not installed.
- R3 (finding 11), on a step 2 failure (a command that exits non-zero, runs past its limit or cannot start), update still runs the install-cli of each tool whose plugin step 2 moved before the stop, then stops with the failure, exit 1 as today. Under the FAIL one line names the commands placed. A placement that fails stops the placing; the step 2 failure stays the FAIL. An interrupt places nothing.
- R4 (findings 12 and 13, update's lines alone), each `next:` update prints is a command alone, its reason on the line above (`hint.update.setup`, `hint.update.held`; `hint.update.held.ps` is folded into `hint.update.held`). A named tool that is listed and not installed: no `everything is current`; the reason line says it is not installed and the `next:` is `agentik setup <tool>`, exit 0 as today. A name that is no tool: `<name> is no known tool` (`err.update.unknown`), exit 2 as today. Update's rows no longer say `setup would …` or `setup leaves …`: `detail` shows update's own words for those of setup's step 4 and 5 ids (`update.say.*`); the step's `mid` is unchanged.
- R5 (finding 15, one part), an interrupt while a command runs: `Update was interrupted, so it stopped <command>`, then `next: agentik update`, exit 130; the journal's `ran` holds the stopped command with exit null. The `still running` line and a `kill -9`'s journal are `apply.py`'s: one NICE row, S4.
- R6, up2's suite row and hints, `doctor.py` and `remove.py` are left as they are. The doctor's own `next:` inside update's screen is the doctor's.
- R7, tests first, red at the pin; each message added holds design/23 §8 and the width test; the version `0.7.31` alone in the last commit.

## 3. Acceptance

| # | line | at the pin (17f4ed5) |
|---|---|---|
| 1 | an update that moves one tool: the close holds the sessions line once; one that moves nothing, none | no such line anywhere |
| 2 | the relay (its `page`) moved 0.2.3 to 0.2.4, a stand-in command at `~/.local/bin/agentik-relay`: its close row is `note`, names the path, the page's line under it; the plan's step 3 row says nothing of setup | `ok  relay 0.2.3 to 0.2.4`; `… setup leaves it as it is` |
| 3 | three tools, the second's plugin update fails: murmur's command is at 1.1.0 after the failed call, the FAIL's next line names it; the second call moves paint and quill and reads `murmur 1.1.0, already current` | murmur's command at 1.0.0; nothing says so |
| 4 | each `next:` update prints (a held run, a tool not installed, a tool gone, a name that is no tool, the suite's close, an interrupt), run by `sh -c` in the temp home, starts and takes its words | `next: … setup quill installs quill, since update installs nothing.`; `next: … update once it has ended` |
| 4a | `update quill` (listed, not installed): no `everything is current`, exit 0; `update nosuch`: `nosuch is no known tool`, exit 2 | `everything is current; nothing was placed.`; `nosuch is not a plugin name: …` |
| 5 | SIGINT to the run while a stub `claude plugin update` hangs: the FAIL names the command, exit 130, the child stopped, the journal's `ran` holds it | `Update was interrupted between steps`; `ran` omits it |
| 6 | `make voice` exit 0; `make check` green through the gate; hygiene over `main..HEAD` exit 0 | green |

## 4. The fix of review 1 (pin ffabf25)

- F1, a prerequisite missing (`claude` not on PATH): the close is a reason line, `step 1 needs <missing>` with Claude Code's address where `claude` is the one missing, then `next: agentik update` with the names given, alone. Setup's `hint.setup.blocked` stays as it is, and update no longer prints it.
- F2, a step 2 failure begins the placing: the list of commands placed is `_run`'s, so an interrupt or a failure during the placing keeps it. Under the FAIL: `placed before the stop:` with that list, the step 2 failure that began the placing (where the FAIL is another's), and a placement that failed (lead L5); the `next:` stays last.
- L1, update's step 1 and step 3 rows (`setup.cmd.missing`, `setup.python.low`, `setup.plugin.missing`, `setup.plugin.broken`) are in update's words (`update.say.*`), as R4 has it; setup's screen is unchanged.
- Leads L2 to L4 and L6 to L8: one NICE row, S4.

| # | line | at ffabf25 |
|---|---|---|
| 7 | no `claude` on PATH, `update --yes`: a reason line naming `claude` and its address, then a `next:` that runs as printed, exit 2 | `next: install claude, then … update --dry-run again.`; pasted, exit 64 |
| 8 | three tools move, quill's plugin update fails, murmur placed, paint's `install-cli` interrupted: `placed before the stop: agentik-murmur 1.1.0` and quill's update named under the FAIL, exit 130 | the FAIL and `next:` alone |
| 9 | the same, paint's `install-cli` failing: a line names it under the FAIL, exit 1 | the `running` line alone |
| 10 | update's screen holds no `setup would`, `setup stops` or `setup leaves`; setup's dry run unchanged | `not on PATH; setup stops here …`; `… setup would install it again` |
