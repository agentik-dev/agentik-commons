# Packet dr1-door-ahead: an older `agentik` earlier on PATH is named, with a fix that mends it

| item | value |
|---|---|
| from | agentik-hq's brief dr1-door-ahead of 2026-11-16, R1 to R4; level S3; the install and upgrade review's findings 10 and 16 |
| pin | agentik-commons main 17f4ed5 (suite 0.7.29); worktree `.claude/worktrees/dr1-door-ahead`, branch `dr1-door-ahead`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME, a temp PATH and a stub `claude`; no network |
| may touch | `plugins/suite/lib/agentik_suite/doctor.py` (`door()`, `_under`'s first lines), `messages.md`'s `doctor.door.*` and `hint.setup.blocked.old`, `plugins/suite/lib/scaffold/hq/Makefile`, `tests/test_dr1_door_ahead.py`, `tests/test_ak11_init.py` (the Makefile's sha and its `make -n` text), `tests/test_ic1_close.py` (the refusal's text), `tests/test_sc2_name.py` (its older-door screen closes on the PATH line), `design/voice/checked.sha256`, `plugins/suite/.claude-plugin/plugin.json`'s version, this packet, `history/sittings/*.md` |
| verify | `make voice` and `make check`, each through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` |

## 1. The owner's words

"Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

The review (finding 10): with a 0.1.0 door first on PATH, `agentik doctor` is the old door's refusal, and `agentik-suite doctor` says `too old to pass a verb to the suite` with `next: ... install-cli`, which answers that `~/.local/bin/agentik` is current and leaves the FAIL standing; with a 0.2.0 door first every verb passes and the doctor still says `too old`. (Finding 16): the old-Python refusal does not name AGENTIK_PYTHON, the way out; the hq scaffold's Makefile runs `shasum`, which a default Fedora or RHEL and a minimal Debian lack.

## 2. Rulings

- R1, where `~/.local/bin/agentik` stands (a regular executable file) and the first `agentik` on PATH is another file, older than this command's door, the door row names that path and its version, and its `fix:` is `plan.PROFILE_LINE`, a command alone; `--json` carries the same remedy. Below 0.2.0 (prog.FLOOR) the row is a fail, `doctor.door.ahead.old`; at or above it a warn, `doctor.door.ahead`. The doctor's close names the same line. No line tells a person to remove a file.
- R2, `too old to pass a verb` (`doctor.door.behind`) is said only of a door below 0.2.0; `~/.local/bin/agentik` at 0.2.0 or newer and older than this command's is a warn, `doctor.door.old`, its remedy as at the pin (`install-cli` where the suite's command is on PATH, else setup).
- R3, `hint.setup.blocked.old`, the refusal's close at the pin (setup's and update's), names AGENTIK_PYTHON; the scaffold's `recordlint` target runs `shasum -a 256` where it is on PATH, else `sha256sum`, both `-c --status`.
- R4, the doctor's other rows are other builders'; `setup.python.low` (step 1's row, which another row builds on now) and `err.setup.blocked.old` keep their words.
- Kept as at the pin: no door at `~/.local/bin` with an old one on PATH (`install-cli` places it; R1's row follows); a door ahead whose version reads newer, or none.
- Tests first, red at the pin, in temp HOMEs with a stub `claude`; each message added or changed holds design/23 §8 and the width test; the version `0.7.32` alone in the last commit.

## 3. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `tests/test_dr1_door_ahead.py` test 1: a 0.1.0 door first on the temp PATH over a setup in the temp HOME: `FAIL door` names `~/old/agentik` and 0.1.0, then `fix: export PATH="$HOME/.local/bin:$PATH"`; the close is the same line; `--json` remedy the same; that line pasted into `sh -c` before `agentik doctor` reads ok, no FAIL | `FAIL door ~/old/agentik is at 0.1.0, too old to pass a verb to the suite`, `next: ~/.local/bin/agentik-suite install-cli` |
| 2 | test 2: a 0.2.0 door first: a `warn door` row naming it and 0.2.0, the PATH line under it and last; no `too old`; `~/.local/bin/agentik` at 0.2.0 alone: no `too old`, a warn | `FAIL door ... is at 0.2.0, too old to pass a verb to the suite` in both |
| 3 | test 3: no door ahead, a newer one ahead, an old one with none at `~/.local/bin`: as at the pin; the ak3d and ic1 suites green unchanged in their door lines | green |
| 4 | test 4: a copy of the scaffold, PATH a folder of a `sha256sum` stand-in, `python3` and an `agentik` stub: `make check` exit 0 and the stand-in ran; a changed `recordlint` red; with `shasum` there it is the one run | `/bin/sh: shasum: command not found`, exit 2 |
| 5 | the old-Python refusal's last line names AGENTIK_PYTHON (test 3 of `OldPythonTest`, ic1's F2 tests) | `This needs a Python of at least 3.99, and 3.9.6 is older.` |
| 6 | `make voice` exit 0; `make check` green through the gate; hygiene over `main..HEAD` exit 0 | green |

## 4. Not built

`agentik --version` printing the door's version in the same form as `agentik version`'s suite version (finding 10's last clause): not in the rulings. The door ahead's own refusal words (`agentik-update ... comes from agentik-dev/agentik-update`) are an old file's and stay. Finding 16's launcher read (`/usr/bin/python3` taken first) is held: the refusal now names the way out.
