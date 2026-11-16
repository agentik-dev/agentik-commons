# Packet lx1-ps-linux: the process list is read on Linux

| item | value |
|---|---|
| from | agentik-hq's brief lx1-ps-linux of 2026-11-16, R1 to R8; level S2; the install and upgrade review of 2026-11-16, findings 1 and 14 |
| pin | agentik-commons main 93f0202 (suite 0.7.24); worktree `.claude/worktrees/lx1-ps-linux`, branch `lx1-ps-linux`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME with a stub `claude`; made-up tool names |
| may touch | `scripts/agentik_install.py` `processes()` and the module's docstring, its copy `plugins/suite/lib/agentik_install.py`; `plugins/suite/lib/agentik_suite/update.py` `hold()`, `Update.held()`, `Update.main()`; `remove.py` `Remove.held()`, `main()`, `run()`, `take()`; `doctor.py` `read()` and one new check; `messages.md` (new ids only); `design/voice/checked.sha256`; `tests/test_lx1_ps_linux.py` (new); `NICE_TO_HAVE.md` (one row); `plugins/suite/.claude-plugin/plugin.json` (the version, last commit alone); this packet |
| verify | `make voice`, then `make check` last, each through the gate queue |
| acceptance | 1 to 6 below; verify green |

## 1. The owner's words

"Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

The finding: on Linux every `agentik update` and `agentik remove` is refused, `--dry-run` included, with `held install: the process list cannot be read` and `next: ... once it has ended`, and `install-cli` never prunes. procps refuses `ps -axwwE` (no `E` in either of its parsers: `must set personality to get -x option`, then `unsupported option (BSD syntax)`, exit 1). Read from procps's source, never run on Linux.

## 2. Rulings

- R1, `processes()` reads with `ps -axwwE -o pid=,command=` as today and, where that exits non-zero, with `ps axwwe -o pid=,command=` (procps's BSD form, whose `e` appends the environment to `command`); the probe check stays and reads either output, and both outputs are `<pid> <command and environment>`, so the parse is the same. It gives no listing only when both fail, and then `why` is `<ps> exited <n>: <the first non-blank line ps wrote on stderr>`, of the second form. A ps that cannot start or runs past its timeout is not run a second time.
- R2, the suite's copy `plugins/suite/lib/agentik_install.py` stays byte for byte the canonical file (`tests/test_agentik_suite.py` holds it). The tools' vendored copies and agentik-session's `prune.py` are other rows'.
- R3, a list that cannot be read: update's and remove's held lines say why (`the process list cannot be read: <why>`), and their `next:` names the same command with `once ps can list each process's environment` in place of `once it has ended`; remove's mid-run stop the same. `install-cli`'s prune line carries R1's why with no change of its own.
- R4, the doctor's suite group gains a `processes` check that reads the list as update does: a warn with the reason where it cannot be read, and no row where it reads, so every doctor screen with a readable list is as at the pin.
- R5, tests first, failing at the pin, against stand-in `ps` files (section 3).
- R6, read from procps's source, not run on Linux; the hq record carries the lines that would prove R1 there.
- R7, finding 14 (bytecode of pruned trees stays under the cache) is one S4 row of `NICE_TO_HAVE.md`. Every message added holds hq design/23 §8 and the width test; `make voice` through the gate.
- R8, other rows build in this repo at once: only the functions above change, no other message; the version `0.7.25` alone in the last commit.

## 3. Acceptance

`tests/test_lx1_ps_linux.py`: PROCPS refuses any word holding `E` with procps's line and exits 1, and for `axwwe` prints its listing and the probe line; BROKEN refuses both forms; PASS_ON refuses the first and passes the second to `/bin/ps`.

| # | line | at the pin |
|---|---|---|
| 1 | with PROCPS: `processes()` reads (both forms run, in order); the prune removes three trees and keeps the live one; `agentik update --dry-run` and `agentik remove --all --dry-run` print their plans, exit 0; `install-cli` prints `prune-trees: removed 2, kept 3 ...` (tests 1, 3, 7, 8) | each fails: `ps exited 1`, exit 2 `held install: the process list cannot be read`, `prune-trees: ps exited 1; keeping every tree` |
| 2 | with BROKEN: `processes()` gives `<ps> exited 1: error: unsupported option (BSD syntax)`; the prune keeps every tree and says it; update's and remove's held lines end `the process list cannot be read: <ps> exited 1: <line>`, `--json`'s `held` the same, and no `once it has ended`; `install-cli` says the reason (tests 2, 4, 9, 10) | each fails: no line of ps's own, `once it has ended` |
| 3 | with BROKEN the doctor's suite group has one `processes` warn naming the reason and `update and remove`; with a list that reads, no such row (test 11) | fails: no row |
| 4 | with PASS_ON a live process naming a tree keeps it through `axwwe` (test 5) | fails: every tree kept, `ps exited 1` |
| 5 | with the real `/bin/ps`, in a temp HOME: `update --dry-run`, `remove --all --dry-run`, `remove x --dry-run --json`, `doctor` and `install-cli` print every line as at the pin (a by-hand diff, temp paths masked); a first form that reads is the only read (test 6) | test 6 passes; 56 lines measured |
| 6 | `make check` green through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` exits 0 | green |

## 4. Not built

The tools' synced copies of the module and agentik-session's `prune.py` (their own rows); the bytecode of a pruned tree (NICE); a run on a Linux machine.
