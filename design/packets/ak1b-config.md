# Packet ak1b: `config`, found from one place and drilled down to one setting

| item | value |
|---|---|
| from | agentik-hq's brief ak1b of 2026-11-13, R1 to R10, and its row's rulings on design/15 §4 P9 to P12, §5.1 (c), §6, §9; level S3 |
| pin | agentik-commons main 8a238f2 (`Merge ak1a-replay`); worktree `.claude/worktrees/ak1b-config`, branch `ak1b-config` |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no ledger; made-up names in fixtures |
| may touch | `plugins/suite/**`; `tests/test_agentik_suite.py`; `design/voice/checked.sha256`; `.hygiene-allow`; `README.md`; `NICE_TO_HAVE.md`; this packet; `history/sittings/2026-11-13-4.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 11 below, each in ak1a's `Home`; `python3 -m unittest tests.test_agentik_suite` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first, the version bump last; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"Make it a high quality modern CLI tool that is dynamic and has high quality concise human friendly feedback (using respeak to help with the voice). Make plugin configuration discoverable and drill down."

## 2. Rulings

- R1, what stands: ak1a's packet, its §7 and §8 too: the floor, `term` the one writer, the catalogue and its voice, the grammar, the streams, `--json` and `Command.fail`, the four exits, `FLAGS`, no tool's name in the package or its tests. A tool's answer is a value from outside: `term` cleans it of control characters; no path or command is cut.
- R2, the tools listed: the suite (`tool_name` less `agentik-`), each `agentik-<name>` on PATH (`_on_path`), each `<name>@agentik` of `installed_plugins.json`.
- R3, `describe`: each executable of R2 but the suite's runs as `agentik-<name> describe --json`, all at once under one 2 s wall; one still running then is killed with its process group. An answer counts on exit 0 and one object with `ok` true and `schema` `agentik.describe/1`, holding `tool`, `version`, `summary`, `repo`, `plugin`, `needs: [{name, kind, why, optional}]`, `verbs: [{name, summary, top}]`, `reads: [{kind, name, argv}]`; an unknown key is ignored. A read's `kind` is `config` or `doctor` (at most one each) or `status`; `argv` is the words after the tool's executable. States: `answers`, `timed out`, `unreadable` (a non-zero exit, no JSON, a schema above 1), `no command` (a plugin with no executable on PATH).
- R4, the cache: a counted answer under `${XDG_CACHE_HOME:-~/.cache}/agentik/suite/`, one file a tool, written by a rename, used while the executable's resolved path, size and mtime hold. Nothing else is cached.
- R5, the config read: the executable with the read's `argv`, a key appended for one setting, same wall. `agentik.config/1`: `layers: [{name, path, present, travels}]`, lowest first; `settings: [{key, value, default, type, choices, summary, source: {layer, path, line}, change: {kind, command, path, block, note}, live, values}]`; `change.kind` `command`, `edit`, `launch` or `fixed`; `live` true takes hold now; `values`, optional, `[{layer, value}]`, lowest first.
- R6, `config`, three levels, each ending in a `next:` hint: `config` (a row a tool: name, state, settings, how many differ, the `user` layer's path); `config <tool>` (key, value, layer, a mark where it differs; past 20 keys grouped by first segment); `config <tool>.<key>`, cut at the first dot, the card (value, summary, default, `set by` layer, file and line, each layer's value, the change, when it takes hold). `--changed`: every differing setting; `--user-files`: each `travels` layer's path, one a line. Exit 0 whenever the read ran; 2 for an unknown tool or key, with the nearest, or a key asked of a tool that does not answer. No write, no `--dry-run`, no `--yes`.
- R7, the fallback table `plugins/suite/lib/fallback.json`, beside the package, with a `.hygiene-allow` row: by tool name, `lines`, `user_file`, `needs`, `status`. A tool that does not answer and has a row is listed with its marketplace `description` (`.claude-plugin/marketplace.json` under `agentik`'s `installLocation` in `known_marketplaces.json`); `config <name>` prints the row. Five rows, the published marketplace's tools; `status` empty.
- R8, the suite's settings: a reader of GUIDE §3's strict subset (nested mappings, scalars, flat lists, `{k: v}` one level deep, comments), refusing anything else by line, keeping each key's line. The user file `${XDG_CONFIG_HOME:-~/.config}/agentik/suite/config.yaml`, written by hand: `checkouts`, a flat list of paths; `watchers`, a name to `match`, `start`, optional `beat` and `writer`. One repo key, `kind` (`hq`), in the `suite` section of `.claude/agentik/config.yaml` of the cwd's repo (the nearest folder upward holding `.git`; no `git`). An unknown key is a `warn` row with its line. A file outside the subset: `config suite` exits 2 with file and line; `config` shows it on the suite's row, exit 0.
- R9, `describe --json` prints R3's object, its one read `{kind: config, name: settings, argv: [describe, config, --json]}`; `describe config --json [KEY]` R5's: layers `user`, `repo`, `travels` false; settings `checkouts`, `watchers.<name>.<field>`, `kind`; `change.kind` `edit`; `live` true. `config suite` reads them in process.
- R10, `help` and the README list `config` and `describe`; `GUIDE.md` untouched.
- Decided (the row, for GUIDE §11 with ak2): a read's `argv` follows the tool's own executable; a setting may carry `values`; `describe` joins the reserved names; the table holds five rows and no private repo's tool; a `config` read is never cached.
- Decided (the builder): a default of null is no default, so it never counts as differing; `describe` without `--json` is exit 2 naming `--json`; a non-answering tool with no row lists as its state alone; a key the tool's answer lacks takes one more read, without the key, for the nearest.

## 3. Acceptance

Each in ak1a's `Home`, made-up tools: `agentik-demo` (three settings, one differing, set at a line of a user file), `agentik-slow` (sleeps 10 s), `agentik-mute` (exits 2), `plain@agentik` (installed, no executable). At 8a238f2 each line prints `config is not a verb` (or `describe`), exit 2; with `--json`, `agentik.usage/1`, code `unknown_verb` (measured).

| # | line |
|---|---|
| 1 | piped: `config` lists `suite`, `demo` (two counts, user file), `mute`, `slow`, `plain` with states; `config demo` three keys, one marked; `config demo.colour` every part of the card; exit 0, no escape byte, a `next:` hint on stderr |
| 2 | under a pty colour and a glyph; `NO_COLOR=1`, no colour |
| 3 | `--json` at each level one object: `tools`; `tool`, `layers`, `settings`; `tool`, `key`, `setting` with `source` and `change.kind` |
| 4 | `config` under 3 s; `slow` `timed out`; the stub's pid gone |
| 5 | a second `config` starts no `describe`; after a stub's mtime changes, one |
| 6 | `config suite` shows `checkouts` with path and line; `suite.checkouts --json` gives `source` `user`, path, line; a temp repo's `suite: kind: hq` beside another section's `{k: v}`: `suite.kind` names that file and line |
| 7 | a user file with a tab: `config suite` exit 2 with file and line, `config` exit 0; `config nosuch` exit 2 with the nearest |
| 8 | the first name of `fallback.json` as a stub exiting 2: listed from the table, `config <name>` prints its lines, `config <name>.x` exit 2 |
| 9 | `describe --json` and `describe config --json checkouts` one object each, R3's and R5's |
| 10 | after each line HOME outside `$XDG_CACHE_HOME/agentik/` unchanged; the stub `claude` recorded nothing |
| 11 | `make check` green after `make voice` |

## 4. Not built

P13's `covers` rule (its first caller, su2 or in4, builds it); `doctor`, `status`, `inbox`, `rows`; setup applied; the door; `install-cli`; version and summary in `help`'s tool list; `status` rows in the table; `GUIDE.md` §11.

## 5. The landing

`plugins/suite/.claude-plugin/plugin.json` to `0.3.0` in the last commit that touches `plugins/suite/`; nothing checks this bump. The coordinator runs the respeak pass over the catalogue (more than ten new messages), then `make voice` again.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list. The report: head sha, gate id and line, acceptance 1 to 11 at the pin and now.

## 7. Review 1's fix

Ruling: all thirteen on the branch, each with a test red at 58db52d; the schema lead rides.
- F1 config reads share the describes' one 2 s wall
- F2 a slow tool adds no time past it
- F3 stdout read to a 1 MiB cap
- F4 no wait on a pipe an escaped child holds
- F5 bad `warnings` dropped
- F6 bad `choices` dropped
- F7 a removed cwd: no repo layer
- F8 the suite's nearest key
- F9 a failed config read named as such at each level
- F10 `--changed`, `--user-files` name the silent tools
- F11 a value outside its choices named
- F12 `config .key`: the name's usage line
- F13 an unopenable file: no line number
- Lead: only `agentik.describe/1` counts

Review 2 closed with no finding; the wording pass changed 13 of its 14 ruled messages (`respeak-verify-edit.py`: PASS); `config.later` keeps its words, since `session` names a tool.
