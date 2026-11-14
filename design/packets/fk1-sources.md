# Packet fk1-sources: one finder says what stands for a tool and which file runs

| item | value |
|---|---|
| from | agentik-hq's brief fk1-sources of 2026-11-13, R1 to R9; hq design/25 §5 (items 1 to 3, 5, 6, 11's key, 16's `mirror`); level S2 |
| pin | agentik-commons main 7bef66c (the merge of `sp1-launcher-step`, suite 0.6.2); worktree `.claude/worktrees/fk1-sources`, branch `fk1-sources`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; every run in a temp HOME; made-up names; no line of `plan.py` edited; the version stays as the pin has it |
| may touch | `plugins/suite/lib/agentik_suite/sources.py`; `plugins/suite/lib/agentik_suite/settings.py`; `plugins/suite/lib/agentik_suite/config.py` (`do_describe` and the `SUITE_SUMMARIES` row); `plugins/suite/lib/agentik_suite/messages.md` (`setting.sources`, after the other `setting.` lines); `scripts/voice`; `tests/fk_homes.py`; `tests/test_fk1_sources.py`; `tests/test_voice.py`; `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-13-16.md` |
| verify | `make voice`, then `make check`, each once, last, through the gate queue, `--strict` |
| acceptance | 1 to 8 below; `python3 -m unittest tests.test_fk1_sources tests.test_voice` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

With a fork installed, `T@acme-tools`, the suite lists no T and plans the marketplace's copy beside it. This row adds the finder and its read. It changes no screen, plan or list. Other builders work in this repo from the same pin, so a shared file is touched only at the place named.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds (§3: the strict subset, unknown keys never fatal).

- R1. `settings.resolve` reads `sources` in the user file, a mapping of tool to value: a plugin id `<name>@<marketplace>`, or a folder, starting `/` or `~/`, the plugin's root holding `.claude-plugin/plugin.json`. Any other value the subset reads is a warning, and the line stands as declared, not found.
- R2. Warnings by reason: `ignored` for `suite.sources` in a repo's file, never read; `self` for `sources.suite`, no line; `relative` for the whole block, ignored when `XDG_CONFIG_HOME` is set and not absolute; `value` for R1's. No variable, flag or verb names or writes a source.
- R3. Each line is a setting `sources.<tool>` from `settings._setting`: layer `user`, file and line, default `<tool>@agentik`, block `sources:\n  <tool>: <id or folder>`, summary `setting.sources`.
- R4. New module `agentik_suite/sources.py`; it starts no process and never imports `tools`. T's candidates are the entries of `installed_plugins.json`, every entry of every id's list, whose plugin is named T: the user's own (`scope` `user`, `managed`, or no `scope`) and the repo's (`project` or `local`, with a `projectPath` that is the cwd or holds it, both resolved). Another project's entry is neither found nor seen.
- R5. What stands, first match: (a) T's line, resolved or not (an id to the user's own entry of that id, else the repo's; an id of another name to nothing; a folder when its manifest reads; unresolved, `found` false and no other root fills in); (b) the only candidate, when it is the user's own; (c) nothing: `undecided` with two or more candidates or one that is the repo's, `absent` with none. `kind` is `own` when the standing id is `<T>@agentik` (declared or not), `plugin` for another id, else `folder`.
- R6. The file that runs: the first `agentik-T` on PATH that is a regular executable, passed over when its resolved path lies under the `installPath` of any entry, of any name or scope, that is not T's standing source; then, and with none on PATH, `bin/agentik-T` under the standing root, or nothing. A PATH file under no plugin's root runs as `placed` when `read_launcher` gives it a tree, else `unknown`. No later PATH entry is tried.
- R7. `describe sources --json [TOOL]`: `{"schema": "agentik.sources/1", "ok": true, "tools": [row]}`; a row: `tool`, `kind`, `plugin`, `root`, `version`, `scope`, `mirror`, `declared` (`{path, line}` or null), `found`, `seen` (each `{plugin, version, scope, root}` not standing), `runs` (`{path, version, of}`, `of` one of `source`, `placed`, `unknown`, or null), `passed_over` (`{path, of}`, `of` an id, or null). With TOOL one row; with none each name of `tools.plugin_names` less the suite, then each declared name. A user file outside the subset: `describe config`'s error, exit 2.
- R8. `mirror` is true when `kind` is `own` and the `agentik` entry of `known_marketplaces.json` records a source other than github `plan.SOURCE`; an `https://github.com/` or ssh (`git` at `github.com:`) URL of it, with or without `.git`, compared without case, is no mirror.
- R9. `scripts/voice`'s scanner keeps `RESPEAK_ROOT` first, then `<root>/scripts/<scanner>` from the finder's row when it stands and is found; `_order` and the cache glob go. Undecided or absent: exit 2, naming `sources`.

## 3. Acceptance

T is `murmur`; U is `T@agentik`; F is `T@acme-tools`. `tests/fk_homes.py` builds each home (a temp HOME; each root at `.claude/plugins/cache/<marketplace>/T/<version>`; a command is `bin/agentik-T` under a root; a launcher holds `VERSION=` and `TREE=`). The terminal's PATH is `~/bin:~/.local/bin:/usr/bin:/bin`. Baseline at the pin: no `sources.py`, no `describe sources` (exit 2, `extra_word`), `sources` an unknown key.

| # | line | at the pin |
|---|---|---|
| 1 | `tests/test_fk1_sources.py`: hA to hK and pA to pC give the brief's `kind`, standing id, `found`, `declared` and `runs` | red: no module |
| 2 | every root's `bin/` on PATH after `~/.local/bin`: hD, pA run the root's file as PATH gives it; hB `runs` null, `passed_over` U's file | red |
| 3 | pB inside its `projectPath`: `undecided`, two `seen`; from HOME the project's entry is in no `seen` | red |
| 4 | `agentik-suite describe sources --json T` in each home: exit 0, one row; no TOOL in hJ: rows for T and paint | red: exit 2 |
| 5 | `describe config --json` warns `ignored` (repo file and line), `self`, `value` for each of R1's five, `relative` (T's `declared` null); `sources.T` a setting at line 2; no `sources` unknown | red: `unknown` |
| 6 | line 4 under a PATH of one empty folder, the interpreter named by path: exit 0, the same rows | red |
| 7 | `tests/test_voice.py`, no `RESPEAK_ROOT`: the fork alone at either version gives its scanner; a leftover folder, and two installed, exit 2, nothing written | red: the glob takes the newest copy |
| 8 | `make voice`, then `make check`, green | green |

## 4. Not built

Every use of the finder and each warning's words (fk2, fk2b); the `tool` equality (ak9b); the other doctors (fk3, fk4); the reporter (fk6); the version (phase 2, on the coordinator's word).

## 5. The landing

The coordinator merges alone, one commons row at a time; `messages.md` gains one line and `checked.sha256` moves with it.

## 6. Forbidden reads and report

No read of `~/.local/state`, a relay ledger or the live home's plugin files by a test. The report: each acceptance line, its exit and last output line; the branch and its head sha.
