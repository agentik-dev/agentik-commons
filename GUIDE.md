# The agentik guide: conventions shared by the tools (r1, 2026-10-13)

Binding on the five tools, agentik-session, agentik-decisions, agentik-respeak, agentik-relay and agentik-agents. Each works alone (R25-91 (3)); these make them consistent, not dependent. §1–§9 are agentik-session's `design/conventions.md` (r1, 2026-09-22) under the new names; that file keeps a pointer here. §10 is agentik-r1's table (`design/agentik-r1.md` §7.2).

## §1 Layout

```
agentik-<tool>/
  <tool>/ or go.mod  the tool (stdlib python or Go), on PATH as `agentik-<tool>` via `make install`
  plugin/  the plugin subtree, self-contained: names no path outside itself
    .claude-plugin/plugin.json
    skills/<name>/SKILL.md  frontmatter: name, description under 200 chars, allowed-tools; body under 500 lines
    commands/<verb>.md  one verb each, under 30 lines
    agents/<name>.md  only where the plugin owns a lane
    hooks/hooks.json  events, by the shim below or the plugin's own scripts
    hooks/run  optional: execs `agentik-<tool> hook <event>` on PATH, else exits 0
    hooks/<name>.ts  optional: the Mod, one `"modules"` entry (§4)
  design/  records `<topic>-rN.md`; packets/ ; readme/source.md
  history/sittings/  charters `<date>-<n>[-<chain>].md`, §3.1 shape (§5)
  scripts/agentik, hygiene, bounded, plugin-version-check  vendored from agentik-commons, pinned in scripts/vendored.sha256 (§5)
  scripts/doclint  the doc gate (§5)
  tests/  the suite (§4)
  Makefile  check, test, lint, doclint, hygiene, validate, readme, install, doctor
  README.md LICENSE .hygiene-allow .gitignore
  relay/queue.yaml  only while the relay runs this repo (D4)
```

A tool repo keeps no `marketplace.json` of its own: two install paths would double the hooks (§2).

## §2 plugin.json and marketplace.json

`plugin.json`: `name` (the short id: `session`, `decisions`, `respeak`, `relay`, `agents`; installed as `<tool>@agentik`), `version` (semver; §7), `description` (under 200 chars, no owner data), `author {name}`, `homepage`, `repository`, `license`, `keywords`; `dependencies` only where needed, as `{name, version, marketplace}` with an npm range; `userConfig` only for install-time knobs (repo config is §3). The one marketplace is agentik-commons' `.claude-plugin/marketplace.json`: `name` `agentik`, `owner {name}`, `plugins: [{name, source: {source: "git-subdir", url, path: "plugin"}, description, version}]`, one entry per tool, checked by `scripts/marketplace-check`. The owner's machine installs from `make local-marketplace`, the same file with `file://` urls, so the IDs match, plus after the five the entries of the owner's overlay (`AGENTIK_MARKETPLACE_OVERLAY`, default `~/.config/agentik/marketplace-local.json`, outside every repo) for a plugin whose repo is not public, which the published file never names.

## §3 Configuration layering, the session as optional provider

Each plugin resolves its own configuration, lowest first: shipped defaults; the user's file (`~/.config/agentik/<tool>/config.yaml`); its section of the repo's `.claude/agentik/config.yaml`; `config.local.yaml` beside it (gitignored); folder and scope files where it has them (respeak); the session's resolved file when present; its session toggles; the invocation.

The resolved file: `${XDG_STATE_HOME:-~/.local/state}/agentik-session/sessions/<session_id>/resolved.json`, written only by `session` at SessionStart and on `set`, shaped `{"provider": {plugin, version, profile, resolved_at, inputs: [{path, sha256}]}, "<plugin>": {..}}`. A plugin takes `session_id` from hook stdin or `$CLAUDE_CODE_SESSION_ID`, the only session variable it reads, accepts the file only when `provider.version` is in its range, applies its section as the layer above, never writes it, and reports it in `doctor`. A plugin reads it only while fresh (agentik-relay's AR75, session-layer-r1 §2): `provider.inputs` lists the plugin's own repo file and the `config.local.yaml` beside it, compared as absolute paths after cleaning, each at the sha256 that file has now (a null matches only a file still absent, an unreadable file has changed); a changed input, inputs that name another checkout's files, or no or a malformed `inputs` makes the layer stale, and the plugin then skips it whole, keeps its own repo and local layers, and gives one warning naming the layer and why, which `doctor` shows as a warning, never a failure. Absent, it runs alone.

The session's own, no dependent's: `CLAUDE_SESSION_DEPTH` (`start` sets parent plus one past its scrub, refuses 2 without `--nested`; the relay sets 1 for its children) and `CLAUDE_SESSION_MAX_TURNS` (set by `start --max-turns`; the turn ceiling is the smaller of it and the profile's). A new variable is named `AGENTIK_*` (§10).

Config files are YAML in the strict subset (D12): mappings, scalars, flat lists, comments. Unknown keys: reported by `doctor`, never fatal.

## §4 The test standard

- **Go** (relay, example-app): table tests over every transition of a state machine; every effect (git, spawn, clock, files) behind a faked interface; an end-to-end test against a fake `claude` of canned stream-json; `go vet` and the race detector in `check`; no network in tests.
- **python** (session, decisions, respeak): stdlib, from `tests/`; a fake `claude` on a temporary PATH, never quota; every hook tested per event from a stdin fixture, exact stdout and exit; the resolver tested per layer pair; byte ceilings tested, not assumed.
- **Mod** (`plugin/hooks/*.ts`): one module per plugin holds every concern (2.1.296: one unmatched hook per event, `$` into no import); `.test.ts` beside it, effects faked, run in `check` by `claude plugin test plugin` (no model); pytest never reads it.
- Every invariant in a design's provability section is one named test; one that can also be a runtime guard is both, the test naming the guard.

## §5 `make check` and the doc gate

`check` runs under `scripts/bounded --lock .check.lock --wall 840 --load 4`: `test`, `lint`, `doclint`, `hygiene`, `validate` (60 s), README freshness (§6), `shasum -a 256 -c scripts/vendored.sha256` (in a repo with a `plugin/`, it also lists the placed `install-cli` module, launcher and door, §10, so a one-byte change in any of them is red), and `scripts/plugin-version-check` (§7). The load rule, as `scripts/bounded` has it: while the 1-minute load is above 4 per core and the CPU's idle share is 25% or less, `bounded` holds the start, polling every 30 s, and after 600 s or at the wall, whichever comes first, exits 2 without running the command; an idle share above 25% at the first reading lets the command start at any load (two readings in a row once it waits), and an unreadable one leaves the load alone to decide. The wall counts from `bounded`'s start, the load wait included. A repository may raise its wall in its own `check` line, kept under the gate's verify limit (the relay's `verify_seconds`, 900 s when unset) so that the wall's stop, read as unrun, comes before the gate's cut; the relay's own `check` keeps 840 s. The lock is a `flock` held by a guardian that kills the command's group when `bounded`'s pipe closes, SIGKILL too. A last stderr line `bounded: stop: lock|load|wall` (exits 2, 2, 124) is unrun, never red; under another `bounded` (`BOUNDED_DEPTH` above 0) it is `bounded: nested stop:`, a plain red. `doclint`'s rules are its docstring: byte ceilings, `NEXT` only as `history/sessions/NEXT`. A packet's `verify` row is the gate line (`make check`); acceptance lines are targeted, rerun by the gate on the branch; doclint's suite rule fails closed from any runner word, passing only a test file, `::`, a `-k`, `go test <pkg> -run <Name>`, `make -n`, or `make` of `MAKE_TARGETED` targets. Packet prompts keep the turns line (`Your --max-turns is N`) until the doctor reads the meter hook live. `pluginlint` is retired at each repo's next re-sync.

## §6 README via respeak, and hygiene

`design/readme/source.md` holds the facts in the technical lane; `make readme` renders `README.md` in respeak's technical mode (`claude -p` or respeak's own script); the invariant is the sidecar `design/readme/rendered.sha256`, not the renderer: two `shasum -a 256` lines (source, README), both from `make readme`. Edit the source, never the README. A README names dependencies by id and range, nothing else outside the repo; no owner path, address, domain, private repo or person in any tracked file. `scripts/hygiene` scans each line, path and link target for its generic groups (home, lan, sibling, secret, email, renamed) and the private list's, owner terms kept outside the repo (`$AGENTIK_HYGIENE_PRIVATE` or `~/.config/agentik/hygiene-private.tsv`); absent: one warning, exit 2 under `--require-private`. `renamed` reads the live files only (agentik-r1 §6.1): outside `design/`, `bugs/` and `history/` and not a `NICE_TO_HAVE.md` or `CHANGELOG*`, plus `history/sessions/PROMPT-*` and `BRIEF-*` and the newest charter of each running chain. A repo declares its running chains in `.hygiene-live`, one chain per line, `-` for the unsuffixed chain; no file means no charter is live. `--json` gives each group `lines` and `files`, allowlisted hits included, and `outside_lines` and `outside_files`, the hits outside the allowlist only; a count of zero is read from `outside_files`. `.hygiene-allow` has exceptions, each row under a `#` reason line (`secret` only under `tests/fixtures/`; `sibling` skipped under `history/sittings/`); counts only, no match or private regex; exit 1 on a hit, 2 on usage. The canonical `scripts/hygiene`, `scripts/bounded` and `bin/agentik` live in agentik-commons; `scripts/sync <repo>` there copies them in and writes `scripts/vendored.sha256`. `scripts/doclint` stays byte-identical across the repos, sha256 `26eaf2c84aadb822f8d63a0257b063afcc0ba6d9bbcf1d2d856abe4c6388341f`, until r2 makes it one copy. Nothing is pushed red; the owner pushes (R25-91 (4)).

## §7 Versioning and the sitting record

Semver; `0.x` may break on a minor and says so in the tag message; a change to a config key, a hook's output, or the resolved-file contract bumps the major; a release's tag `v<semver>` equals `plugin.json` `version`; a `-alpha.N` version needs no tag (and matches no `^` range); the session widens a dependency range only once its suite passes against it. Any change under a plugin's `plugin/` bumps `plugin.json`'s version, an `-alpha.N` included, since Claude Code refreshes an installed plugin only on a new version: `scripts/plugin-version-check` fails when a file under `plugin/` changed after the commit that last changed the version (a bump not yet committed passes), and commons' `make versions` shows a marketplace line that trails it. Sittings carry a charter, commit per act, never `--amend` or push, builders in worktrees (at open, before `make`, `.venv` a symlink to the main checkout's; `make venv` only where it has none); a worktree never writes under `.venv` (no `pip install -e`: E7). A repo not yet moved under hq design/04 keeps this paragraph; a moved one takes §10's `install-cli`. `make install` freezes the committed `<tool>/` by tree hash and runs it with `python -P` (floor 3.11): no checkout runs hooks (T5); it also installs the `agentik` front door from the vendored `scripts/agentik` (D3). The launcher bakes the venv's `bin/python` link (its directory resolved), never the link's target; a `/Cellar/` path is refused. When that interpreter or the frozen tree is gone, a hook says `run make install` once and exits 0; other verbs exit 1. Scripts keep `#!/usr/bin/env python3` (T3: the owner's global line names the exception); gate lines run under `make` or `.venv/bin/python`, never a shim.

## §8 Citing a record

Packets and sitting prompts' read lists cite a record as `record <file> --section SPEC` lines (overhaul-r1 §2.7), never a prose range; READMEs cite sections likewise.

## §9 Packet authoring

- **may touch** is a closed list of full paths from the repo root; it always admits `history/sittings/*.md` and `history/sessions/NEXT`.
- The `verify` row is required (doclint's GRANDFATHERED excepted: 11 in agentik-session, 17 in agentik-relay); each **acceptance** line is targeted (§5; relay's `packet.Unbounded` takes the same cells), with a measured baseline. SPENT (relay's `spent`, ar21) keeps the row, skips the suite rule. In the table every pipe is `\|` (the gate unescapes), so alternation is `grep -E` with a plain `|`; fixed strings, `grep -qF`.
- Six sections, six header rows plus `verify`, under 9,216 bytes. One recorded exception (2026-10-14): commons' spent packet `design/packets/agentik-r1-commons.md`, 9,913 bytes, kept as it was built, since a spent packet is a record.
- A packet's charter opens with doclint's five rows; the budget row says so.
- The builder decides inside the design of record, records each choice in the charter's handover with its consumer, and names at most one open fork for the owner.
- A sitting's records (the merge message to a file outside the repo, the note under `history/sessions/`, the record commit by explicit path) go through the agents plugin's `agents:scribe` by default, where the plugin is installed, on Sonnet, from the hand-back, the repo and the records wanted; the coordinator reads its six lines (a-s14, 2026-10-29; a-s15, 2026-10-31).

## §10 One command surface (agentik-r1 §7.2)

| part | content |
|---|---|
| naming | `agentik-<tool>` for the repo, executable, dist, venv and state folder; plugin `<tool>@agentik`; config in `~/.config/agentik/<tool>/` and `.claude/agentik/config.yaml`; new env vars `AGENTIK_*` |
| front door | `agentik <tool> args…` execs `agentik-<tool>` from PATH with the args unchanged; `agentik` lists the tools on PATH; `agentik help <tool>` runs its `--help`. It reads and writes nothing and resolves no old name. |
| verbs | Words or verb-noun (`setup-key`), never a flag as a verb. `doctor` checks the machine, `status` reads once, `report` writes markdown, `run` drives, `hook` is internal. Every tool has `--help`, `--version` and `doctor`; reads take `--json`. |
| exit codes | Exit codes report the task, not the content. 0: done. 1: a check said no. 2: usage or a failed precondition. 3: not installed (the front door, when `agentik-<tool>` is not on PATH, names its repo `agentik-dev/agentik-<tool>`). |
| docs | READMEs show `agentik <tool> <verb>`; code uses the dash name |
| README shape | The docs-r1 order: Why it exists, What it does, Does it work?, Install, Commands and skills, the tool's own sections, Design of record, Tests, Conventions shared with the sibling plugins, What can go wrong, Status, Layout, License. The sibling paragraph is decisions' wording, kept in `docs/sibling.md`. |
| install, hygiene | BINDIR is `~/.local/bin`. A repo not yet moved under hq design/04: each CLI goes in before its plugin; a moved one needs no order, since its plugin runs without the CLI and `install-cli` is optional. Groups: home, lan, sibling, secret, email, renamed; the private list stays outside the repos. |

**The floor (hq entry 6).** A Python plugin, as it moves under hq design/04, runs its hooks and tools from its own `plugin/lib` through a launcher in its `plugin/bin`, on `AGENTIK_PYTHON`, else `/usr/bin/python3`, else `python3` on PATH, at a runtime floor of Python 3.9 on the standard library alone, and a runtime script in it takes a `#!/usr/bin/python3` shebang. The floor binds a repo from its first packet under that design; until its move a repo stands as it is. A repo's own dev scripts and gates keep `env python3`.

**`install-cli` (hq design/04 §2, §3, §5).** The optional step that puts a moved tool's launcher on the terminal's PATH, with no checkout or venv. `<tool> install-cli [--prefix P]` freezes the code it runs from by content hash under `<prefix>/share/<tool>/<hash>/` (default prefix `~/.local`), writes `<prefix>/bin/<tool>`, a link for the tool's old name when it has one, and the `agentik` door, each by a temp file and a rename, then prunes: it keeps the new tree, each tree a running process names, and the newest three, and on any doubt about `ps` it removes nothing. The canonical forms are commons' `scripts/agentik_install.py` and `scripts/plugin-launcher`; `scripts/sync` places them at `plugin/lib/agentik_install.py` and `plugin/bin/agentik-<tool>`, with the door at `plugin/bin/agentik`, byte-identical in every tool and listed in `scripts/vendored.sha256`. A placed copy under `plugin/` needs a version bump like any other change there (§7), and a re-sync that changes one is a bump.

| what differs by tool | where |
|---|---|
| `tool_name`, `remedy`, `runner`, `old_name`, `old_state` | `plugin/lib/agentik-tool.conf`, one `key=value` a line, every key present, plain words with no quotes; `sync` writes it once from `plugin.json`'s `name` when absent and never again; the tool's own, not listed |
| the runner, `plugin/lib/<runner>` | the tool's own: it puts its own folder on `sys.path` (`-I` leaves it off), imports `agentik_install`, and calls `restore_parent_env()` before it can spawn |
| its calls | `install_cli(prefix)` from the verb, `refresh()` from `hook SessionStart` (a line it returns goes in the `systemMessage`), `version()` for `--version` |

| exits | |
|---|---|
| `install-cli` | 0 done; 1 it could not, one line on stderr, a malformed conf included |
| either launcher, a verb, its interpreter or its runner or tree gone | 3, one line naming the remedy |
| either launcher, a `hook`, the same | 0: `hook SessionStart` says so in a JSON `systemMessage` every time; the written launcher's other events once, by an `install-needed` marker in the state folder that `install-cli` removes |

**The forward-only refresh.** On SessionStart, a plugin newer than the launcher that exists runs the install. It creates no launcher; it refuses a backward or equal version, a version it cannot read, and a link; only the plugin `CLAUDE_PLUGIN_ROOT` names refreshes, never a frozen tree or a checkout; another process holding the lock costs nothing, since a later session sees what it left; and a failure is one line for the `systemMessage`, never a failed hook. `install-cli` by hand may go backward: it is the way down.

**The aliases.** Through r1 the old names keep working as aliases (agentik-r1 §4.3), and r2 ends them on or after 2026-12-31: `claude-code-session`, `claude-code-decisions`, `claude-code-respeak`, `claude-code-agents`, `agent-relay`, `claude-session`, `claude-local`, `claude-agents`, `localrig`, `agentroute`, and the bare `` `relay <verb>`` and `` `decisions <verb>`` forms. `claude-api-agent`, `claude-fanout` and `claude-costs` ended on 2026-10-31 with the verbs they named, on the owner's word (agentik-agents a-s17). An alias gives one note on a terminal and nothing new in hooks or pipes (A3). New text uses only the new names; the `renamed` group holds every live file to that, and this guide's row in `.hygiene-allow` covers this paragraph.
