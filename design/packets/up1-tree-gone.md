# Packet up1-tree-gone: a command whose code is gone is seen and placed again

| item | value |
|---|---|
| from | agentik-hq's brief up1-tree-gone of 2026-11-16, R1 to R6; the install and upgrade review of that day, finding 2; level S2 |
| pin | agentik-commons main 93f0202 (suite 0.7.24); worktree `.claude/worktrees/up1-tree-gone`, branch `up1-tree-gone`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME with a stub `claude`; made-up tool names in fixtures |
| may touch | `plan.py` steps 4 and 5 and one helper beside them, `doctor.py` (`FACT`, `own_doctors`), `messages.md` (four new ids), `tests/test_up1_tree_gone.py` (new), `design/voice/checked.sha256`, the plugin's version line (last commit, alone), this packet |
| verify | `make voice` and `make check` through the gate queue |
| acceptance | 1 to 6 below; verify green |

## 1. The owner's words

"Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

What a person met at the pin, with a launcher's `TREE` folder gone (a hand's `rm`, a restore of `~/.local/bin` without `~/.local/share`): the command says its code is gone and names a slash command; `setup --dry-run` reads its row `ok`, at the plugin's version; `update --yes` says `everything is current; nothing was placed.`; the doctor says `its doctor failed, and printed nothing` and closes on the tool's own doctor, which prints the same refusal. Nothing places it again.

## 2. Rulings

- R1, steps 4 and 5 of the plan read the launcher's `TREE` and its runner as well as its `VERSION`. A tree or runner that is absent makes the row `todo`, `its code at <tree> is gone`, with the source's `install-cli` as its command, whatever the versions say. Step 4 takes `setup.launcher.gone`, step 5 `setup.suite.gone`; step 5's command is this command's own `install-cli`, as for a launcher behind.
- R2, so `setup` and `update` both run that line and place the command again; update never says everything is current over such a row (it counts a placed row, as today).
- R3, the doctor: the launcher's row says the code is gone (`doctor.plan.code`) and its remedy, as for every left step 2 to 5, is `setup` in the command's form, so the close's `next:` runs at a terminal. Where a tool's own doctor fails and prints nothing on stdout, `own_doctors` shows that tool's last stderr line that is not blank (`doctor.tool.said`), cleaned and cut as a tool's line is (`tools.one_line`); no stderr at all keeps `doctor.tool.silent`.
- R4, tests first, failing at the pin, in a temp HOME with a stub `claude`.
- R5, every message added holds design/23 §8 (the voice rules) and the width test; `make voice` through the gate.
- R6, nothing outside the functions above changes; the version `0.7.25` goes alone in the last commit.

## 3. Interfaces

- `plan.code_gone(path)`: the tree the launcher at `path` runs from, when that tree or its runner is gone, else None; never raises. A launcher runs from its tree when its text holds `$TREE` (or an older form's `$CODE`) beside the line that names it; the runner is the first `"$TREE/<word>"` in its text, as install-cli's template writes it. A launcher with no such line (one that never runs its tree) is not read as gone, so a launcher whose tree stands, and any launcher that does not run one, reads as at the pin.
- `own_doctors`: `run_all` is given `errs`; the stderr of the job whose result is read (round 2 where round 1 ran) supplies the line.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `tests/test_up1_tree_gone.py` PlanTest: a tree moved aside, or its runner alone, is step 4 `todo` `setup.launcher.gone` with `<source> install-cli`; the suite's own tree moved aside is step 5 `todo` `setup.suite.gone` with this command's `install-cli`, the door ok; a launcher whose tree stands, and one that never runs its `TREE`, read as at the pin | three fail: `ok`, `setup.launcher.ok` / `setup.suite.ok` |
| 2 | SetupUpdateTest: `setup --dry-run` shows the `todo` row and its line; `setup --yes` and `update --yes` place it, the tool answers `--version`, update does not say `everything is current`; a second update does | three fail: the row reads `at version 1.0.0, the same as the plugin`; update says `everything is current; nothing was placed.`; `--version` exits 3 |
| 3 | DoctorTest: `doctor` names the gone code, shows the tool's stderr line, its one `next:` is `agentik setup`, and that line run on a terminal with `y` places the command, which then answers `--version` | fails: `FAIL session its doctor failed, and printed nothing`, the suite's group ok |
| 4 | DoctorTest: a silent doctor's last stderr line stands in place of `printed nothing`; none on stderr, or text on stdout, read as at the pin | one fails |
| 5 | `make voice` exits 0; `tests/test_sc1_voice_width.py` passes | n/a |
| 6 | `make check` green through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` exits 0 | green |

## 5. Not built

A launcher newer than this command whose tree is gone is placed again from this command, so it moves backward; that follows R1's "whatever the versions say". The command's own refusal still names its slash command: that text is each tool's launcher template, not the suite's.
