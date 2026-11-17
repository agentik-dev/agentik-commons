# Packet ic2-needs: setup names each plugin's need before the yes, and plans only what it can do

| item | value |
|---|---|
| from | agentik-hq's brief ic2-needs of 2026-11-16, R1 to R4; the first-install review's findings 7, 13 and 14; hq design 15 section 7.1; hq design 23 section 8 (the voice rules); level S3 |
| pin | agentik-commons main 17f4ed5 (suite 0.7.29); worktree `.claude/worktrees/ic2-needs`, branch `ic2-needs`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; every probe in a temp HOME with a stub `claude` and a stand-in `python3`; made-up names in fixtures |
| may touch | `plugins/suite/lib/agentik_suite/plan.py` (step 1, a `known` helper, the module's docstring), `plugins/suite/lib/fallback.json` (respeak's row), `cli.py` (`do_setup`'s refusals), `apply.py` (`STATUS`, one state), `doctor.py` (`plan_rows`, `STATE`, `_rows`' one line that shows a note), `messages.md` (new `setup.need.*`, `err.setup.unknown`, `err.setup.home`, `doctor.plan.absent`), `design/voice/checked.sha256` (by `make voice`), `tests/test_ic2_needs.py` (new), the tests that plan a made-up name not known at their pin, `NICE_TO_HAVE.md` (one S4 row), `history/sittings/2026-11-16-1-ic2-needs.md`, `plugins/suite/.claude-plugin/plugin.json` (the version 0.7.33, alone, last), this packet |
| verify | `make voice`, then `make check` once, last, through the gate queue |
| acceptance | 1 to 5 below |

## 1. The owner's words

"Use up to 2 Fable agents to review our upgrade/install so far. Use up to 8 opus agents to build anything to help us with install/upgrade concerns." His standing ask: "setup and doctor usable today".

## 2. Rulings

- R1 (finding 7), step 1 has one row for each chosen plugin's need that is not met (design/15 §7.1), a `warn` that names the need and the plugin, shown before the yes; `fallback.json` gains respeak's row. Setup still goes on after a yes. The doctor's `fix:` line for the need, the tool's own, stays as it is; that a Homebrew Python refuses it is one NICE row, S4.
- R2 (finding 14), a name outside the known plugins is refused before the plan, at the dry run too, in words that say it is no known plugin; with HOME unset setup refuses and plans nothing.
- R3 (finding 13), the doctor checks the plugins that are installed; the absent default ones are one note, and they alone never make the close `next: agentik setup`.
- R4, stay in step 1, `build`'s refusals and `plan_rows`; step 4, the door row and the closes are other builders'.

## 3. Interfaces

- A need is a word of a plugin's `needs` list in `fallback.json`. `plan.NEEDS` says how each is read: `Go` is `go` on PATH; `PyYAML` is `python3` on PATH that imports `yaml` (`python3 -c "import yaml"`, run from `/`, stdin closed, a 2 s wall; any exit but 0 is not met). A word with no reading makes no row. Respeak's row: `needs: ["PyYAML"]`, `lines: ["agentik respeak doctor"]`, `user_file: null`.
- A need not met is a step-1 row: id `need`, state `warn`, subject the need, message `setup.need.missing` naming the plugin, no command. `warn` is a new step state: the plan's table marks it `warn`; nothing counts it as blocked, so setup runs on; it is not `ok`, so the dry run's close reads `hint.setup.rest`, not `.done`, where it stands. `--json` carries `state: "warn"`.
- The doctor does not show the `need` row: the tool's own doctor names it, with its `fix:`.
- Known names: `plan.known(env, lib)`, `tools.known` (the marketplace file's, the fallback table's, each installed `<name>@agentik`, each `sources` line's) and `suite`. `setup` with a name outside them refuses with `err.setup.unknown`, exit 2, before any read of the plan, its remedy the dry run of the default set. HOME unset or empty: `err.setup.home`, exit 2, remedy null. Both before `--dry-run` forks from the run.
- `doctor.plan_rows` plans the installed plugins: the default set's that are installed, in its order, then each other known name installed, sorted, the suite's own left out. The default names not installed are one `note` check, `plugin`, `doctor.plan.absent`, no remedy; `_rows` shows it on the screen as it shows a warn.

## 4. Acceptance

Each in a temp HOME, PATH `~/.local/bin`, a folder with a stub `claude` (the plan tests' stub) and a stand-in `python3`, then `/usr/bin:/bin`; the suite starts as `./setup` from the worktree.

| # | line | at the pin |
|---|---|---|
| 1 | a stand-in `python3` with no `yaml`: `./setup --dry-run respeak` and `./setup respeak` on a terminal show a step-1 warn naming PyYAML and respeak above the question; with `yaml` there, no such row (`-k test_r1`) | step 1 reads claude, git, python3 ok; no row names PyYAML |
| 2 | `./setup --dry-run nosuch` and `./setup --yes nosuch`: refused, exit 2, the words say it is no known plugin, no `known_marketplaces.json` written; HOME unset: refused, exit 2 (`-k test_r2`) | both exit 0; the run adds the marketplace and installs `nosuch@agentik`; HOME unset plans `.local/bin/agentik-session` |
| 3 | `./setup --yes respeak`, then `agentik-suite doctor`: one note naming session, decisions and agents, and the close does not name setup (`-k test_r3`) | `warn plugin not installed: session@agentik, decisions@agentik, agents@agentik`; `next: ~/.local/bin/agentik-suite setup` |
| 4 | `./setup --yes`, then the doctor: the suite group's rows and close as at the pin (`-k test_r4`) | `warn suite 1 to look at, 15 ok`, the door's warn alone, no `next:` |
| 5 | `make voice` exits 0; `make check` green through the gate; `scripts/hygiene --require-private --commits main..HEAD` exits 0 | green |
