# Packet fk2-plan: the suite lists and runs what the finder names, and setup plans by it

| item | value |
|---|---|
| from | agentik-hq's brief fk2-plan of 2026-11-13, R1 to R8, and the coordinator's start line of 2026-11-14; hq design/25 §3 items 4, 5, 6, 9 and 12, §9; level S2 |
| pin | main at 43e902e (suite 0.7.2: sp1, fk1, sc4, su2 and rp6 landed); worktree `.claude/worktrees/fk2-plan`, branch `fk2-plan`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test runs `setup` without `--dry-run` or outside a temp HOME; made-up names (`murmur`, `acme-tools`); no version (the start line) |
| may touch | `plugins/suite/lib/agentik_suite/tools.py`, `plan.py`, `apply.py`, `cli.py` (setup's detail takes the slots), `status_read.py` (R3), `messages.md` (`## Setup`); `tests/fk_homes.py`, `tests/test_fk2_plan.py` (new), `tests/test_agentik_suite.py` (line 9); `NICE_TO_HAVE.md` (one row); `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-14-3.md` |
| verify | `make voice`, then `make check`, each once, last, through the gate queue, `--strict` |
| acceptance | 1 to 11 below; `python3 -m unittest tests.test_fk2_plan` OK |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The finding, measured again at 43e902e

In fk1's homes with a stub `claude`, the `agentik` marketplace's file listing `murmur` and each command logging to `$HOME/ran.log`: in `hA` (the fork alone) `setup --dry-run murmur` plans `claude plugin install murmur@agentik` at step 3, and `config --json` and `doctor --json` list the suite alone; so in `pA` and `hD`, where the fork's command is off PATH. In `hB`, `hH` and `hI` step 3 reads `murmur@agentik` ok, and in `hI` step 4 plans the marketplace copy's `install-cli` over the fork's launcher. In `hJ` both `murmur` and `paint` plan `claude plugin install <name>@agentik`. In `pB` step 3 reads the project's 0.11.0, the first entry of the list. In `hB` with both `bin/` on PATH, `config` and `doctor` run the marketplace copy's command (`describe`, `doctor --json`, `doctor`). `pC` reads ok at step 4 and names `~/.local/bin`'s launcher at step 7, while `~/bin`'s 0.12.6 runs first.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. fk1's finder (`sources.find`) gives a tool's row: `kind` (`own`, `plugin`, `folder`, `undecided`, `absent`), `plugin`, `root`, `version`, `declared`, `found`, `seen`, `runs`, `passed_over`. T is a tool's name.

- R1. The names the suite knows (`tools.known`) are `tools.descriptions`, `tools.fallback`, each `<name>@agentik` in installed_plugins.json, and each `sources` line's. `tools.installed` gives those whose kind is not `absent`; a plugin of another marketplace whose name is none of these is no tool. `plugin_names` takes the `sources` lines too.
- R2. `tools.listed` gives each entry `exe` as the finder's `runs.path`, or None, and a key `source`, the finder's row (None for the suite and a name found on PATH alone). A name found on PATH alone is listed as today. `config.Reader.survey` and `doctor.own_doctors` run that file with a read's words.
- R3. The suite starts no file under the root of a candidate that does not stand: no `describe`, `doctor`, `install-cli`, nor a status read (`status_read` takes the finder's file where it passes PATH's first over).
- R4. Step 3 by each name's row: `own` found, today's row byte for byte, from the standing entry; `plugin` or `folder` found, `ok`, the id or the folder as `plan.shown` gives it, the version as the source gives it; `absent`, or `own` not found, today's rows, `claude plugin install <T>@agentik`; `plugin` or `folder` not found, `todo` with no command, declared at `path:line` and not installed, and no step 4 or 7 for T; `undecided`, one held row in place of steps 3, 4 and 7, with how many plugins of the name are installed and `config suite.sources.<T>`, a second message for a lone plugin a repo's settings brought.
- R5. Step 4 for a source that stands and is found, R its root, W `~/.local/bin/agentik-T`: `runs.path` neither W nor under R and earlier on PATH than W, `todo` with no command naming it; W a link to a file under R, `ok`; else today's rows from R and the standing version, `install-cli` from R only for a command that takes it. W's `VERSION` against the standing version by equal strings first; where they differ for a source not `own`, both strings, neither called behind. Where no W is placed, today's `missing` and `inplace` rows stay (ruled 2026-11-13).
- R6. Step 7's line names `runs.path`.
- R7. A row with no command is never run (`apply.runnable`) and is nothing to do for `apply.planned` and `cli.Command._closing`. `apply.install_root` takes the finder's root.
- R8, not built here: `sources.py`; `cli.Command._not_a_verb` (ak9b); the doctor's and config's screens, the `from` line, and `doctor.plan_rows`'s remedy for a held row (fk2b).

## 3. Acceptance

T is `murmur`; U `murmur@agentik`; F `murmur@acme-tools`; the homes are `tests/fk_homes.py`'s, which gains the marketplace's file listing T, a stub `claude`, and a command that appends to `$HOME/ran.log`. Lines 1 to 6 read `plan.build` and `setup --dry-run murmur --json`.

| # | line |
|---|---|
| 1 | hA: step 3 `ok`, subject F; no command holds `plugin install`; step 4 `setup.launcher.none`. Pin: step 3 `todo`, `claude plugin install U` |
| 2 | hB, hH, hI: exactly one step names T, `todo`, command null. Pin: step 3 `ok` U, and in hI step 4's `install-cli` |
| 3 | pC: line 2's row. With the user line `murmur: U`: step 3 `ok`; step 4 `todo`, no command, naming `~/bin/agentik-murmur`. Pin: step 4 `ok` |
| 4 | pB with a command under each root, from HOME: no `todo` row for T; step 4 `setup.launcher.ok`. Pin: `setup.launcher.behind` |
| 5 | hJ with `paint`: paint's step 3 `todo`, no command, the file and line 3; no step 4 or 7 for paint. Pin: `claude plugin install paint@agentik` |
| 6 | hG: today's install row for U. F installed with the line `murmur: U`: step 3 `todo`, `claude plugin install U` |
| 7 | `config --json` and `doctor --json` at the terminal's PATH in pA and hD: `ran.log` holds F's lines. hB with a command under each root and both `bin/` on PATH: `ran.log` empty. Pin: empty in pA and hD, U's lines in hB |
| 8 | `config --json` in hA lists T. Pin: the suite alone |
| 9 | the suite's tests pass under `python3` and `/usr/bin/python3` |
| 10 | the plan's wall time over a five-plugin home, before and after, in the record. Pin: `plan.build` 0.72 ms median in process, `setup --dry-run --json` 48 ms |
| 11 | `make voice`, then `make check`, green |

Each caller of `tools.listed`, `tools.installed` and `plugin_names` the brief does not name keeps its bytes for a tool whose kind is `own`, with a test.

## 4. Not built

The doctor's and config's screens and warnings (fk2b); the `tool` equality and the dispatch of a plugin's word (ak9b); the forward refresh at SessionStart (a NICE row); the version (phase 2).
