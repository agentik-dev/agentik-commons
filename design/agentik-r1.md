# agentik-r1: one command surface, and agentik-commons

Record r1, 2026-10-13, folded after its refuter round (an architecture change: the round precedes code).

**The owner's word (2026-10-13, 14:15).** One git-style `agentik` front door runs `agentik-<tool>` from PATH. Each plugin installs on its own, and the old names stay as aliases for a while. agentik-commons is public and holds the guide, the canonical hygiene, shared code and one `agentik` marketplace.

**Private rollout notes.** The owner's repos, machine, ledger text, running sessions and paste lines are in private notes outside this repo; this record names them only by kind.

## §1 The problem

Five tools, five naming schemes, three marketplace rules. One tool takes verbs as flags. `claude-code-session` is a marketplace, a state folder and a config folder.

## §2 The survey (read-only, 2026-10-13)

### §2.1 Executables

| repo | executable, where | verbs today |
|---|---|---|
| relay | `relay` (Go `cmd/relay`), `~/go/bin` | status resume report attach plan run stop kill gate clean doctor version; `hook` (internal) |
| session | `claude-session` (`~/.local/bin`), a sh launcher; frozen trees in `~/.local/share/claude-session/` | start config doctor profile set checkpoint status report charter rules budget run; internal: mod admission measure hook |
| decisions | `decisions`, uv tool `claude-code-decisions` | show find new ask answer render doctor backlog |
| respeak | none | — |
| agents | 8 links in `~/.local/bin`: `claude-{api-agent,fanout,costs,agents,local}`, `localrig`, `agentroute`, `queue-mvp` | `claude-api-agent` has `--setup-key --key-status --edit-key --remove-key --list-profiles --pin-proxy --usage --wrapper-help` |

`bounded` and `hygiene` (acc3498d) match in all five; `doclint` in three.

### §2.2 Plugins

| plugin@marketplace | commands · skills · agents | hooks → CLI |
|---|---|---|
| `agent-relay@agent-relay` | status plan gate report resume doctor · — · builder adversary attendant | `hooks/run`: `$RELAY_BIN hook`, else `relay hook` |
| `session@claude-code-session` | checkpoint doctor profile report set status · session read · — | `hooks/run`: `claude-session hook` (9 events); `session.ts` runs `claude-session` |
| `decisions@claude-code-decisions` | answer backlog find new render show · ask decisions · — | — |
| `respeak@claude-code-respeak` (GitHub) | — · respeak include init off on report · respeak | its own scripts |
| `claude-code-agents@…` (disabled) | agents-status, delegate-* · delegated-review, local-delegation · local-* | — |

Each plugin's `allowed-tools` names its CLI. Plugin data folders are empty; no user hook or permission rule names an old CLI.

### §2.3 Callers outside the five repos

Files and lines are in the private rollout notes.

| kind | what |
|---|---|
| session briefs | 27 in the consumer repos, 3 read by running launchers, plus each chain's newest charter |
| start lines | `claude-session run …`, pasted by hand |
| subagent types | `agent-relay:builder`, `:adversary`, `:attendant` in briefs and live packets |
| repo config | `.claude/claude-code-session/config.yaml`, with an `agent-relay:` section |
| CLAUDE.md, ledger | generated `decisions` lines; four ledger entries name the old surface (§8.0) |
| a repo template | `decisions render --check` in its Makefile |
| the owner's machine | five old plugin IDs in user settings; `~/.local/bin`; `~/go/bin/relay` |

Files with hits: `claude-session` 50, `relay <verb>` 443 (mostly prose), `decisions <verb>` 140, agents tools 26, `agent-relay:*` 29.

### §2.4 Facts that bind the design

- **Plugin names have no aliases.** Renaming a plugin renames every `/<plugin>:<cmd>` and `<plugin>:<agent>`.
- **Cross-repo entries validate.** `claude plugin validate` accepts `git-subdir` entries, including `ref`, `sha` and `file://` urls. It refuses `..` and absolute paths only in a string source.
- **decisions writes its own name into blocks.** `render.py:59` writes "by `decisions render`" into every generated block, so a new wording makes each `render --check` stale.
- **relay's guards match by name.** They match `^claude-session` (`guards.go:815`) and the basename `relay` or `cmd/relay` (`:66,108`). A new spelling gets past both.
- **Session's README test requires the old CLI.** Its `test_readme` requires `claude-session report` and `claude-session doctor`.
- **Launchers keep their code.** A running `claude-session run` keeps its interpreter and tree until the owner restarts it (a RESPAWN restarts only `claude`). Three ran during the survey, one from the pre-move folder.
- **hygiene's exit codes are reversed.** It exits 2 on a hit and 1 on usage.

## §3 The front door `agentik`

| item | decision |
|---|---|
| language | POSIX `sh`, under 100 lines: no interpreter, no build |
| dispatch | `agentik <tool> args…` checks `<tool>` against `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, then `exec`s `agentik-<tool>` from PATH with the args unchanged. It reads and writes nothing and resolves no old name. |
| listing | `agentik` (or `help`) lists each `agentik-*` on PATH, first in PATH order winning; `agentik help <tool>` runs the tool's `--help`; `--version` gives the front door's version |
| exit | 0 for list, help and version, even when nothing is found; the tool's own code on dispatch; 2 for usage; 3 when `agentik-<tool>` is not on PATH, naming its repo (relay's commands already read 3 this way) |
| home | `bin/agentik` here; each tool repo vendors `scripts/agentik`, hash-pinned, and `make install` copies it to BINDIR (D3) |

## §4 The tools

### §4.1 Names

| tool | new | install | old name, alias until 2026-12-31 |
|---|---|---|---|
| relay | `agentik-relay` | `go build -o ~/.local/bin/…` | `relay`, a symlink; `~/go/bin/relay` becomes a link |
| session | `agentik-session` | `make install`; trees in `~/.local/share/agentik-session/` | `claude-session`, a symlink |
| decisions | `agentik-decisions` (dist renamed) | `uv tool install .` | `decisions`, a second entry point |
| respeak | none in r1 (D4) | — | — |
| agents | `agentik-agents`, a sh dispatcher | `make install` | the 8 scripts, kept as they are |

Verbs stay, except agents'; session gains `--version`, agents `doctor`.

### §4.2 agents' verbs

| `agentik agents …` | runs |
|---|---|
| `api [profile] …` | `claude-api-agent …` |
| `setup-key key-status edit-key remove-key pin-proxy usage` | `claude-api-agent --<same>` |
| `profiles` · `help api` | `--list-profiles` · `--wrapper-help` |
| `fanout costs local` · `status fold` | `claude-fanout`, `-costs`, `-local` · `claude-agents status`, `fold` |
| `rig …` · `route …` · `doctor` | `localrig` · `agentroute` · today's `make doctor` checks |

`queue-mvp`, an experiment, gets no verb.

### §4.3 The aliases

- **Form.** The old name points at the new code, with no shim, so the hook path is unchanged.
- **Note.** Under the old name, with stderr a terminal and a verb other than `hook`: one stderr line, `claude-session: renamed; use 'agentik session …' (ends 2026-12-31)`. Hooks, pipes and gates see nothing.
- **End.** 2026-12-31, in r2, once `renamed` (§6.1) finds no live caller. The date can only move later.
- **Printed lines.** `agentik relay resume <row>`, `agentik session run --chain <name>`.
- **render.** Its wording stays until r2, which re-renders each scope once.

## §5 Plugins, the marketplace, skill namespaces

### §5.1 Plugins

| before | after | namespaces |
|---|---|---|
| `agent-relay@agent-relay` | `relay@agentik` | `/relay:status` and the other five; `relay:builder`, `relay:adversary`, `relay:attendant` |
| session, decisions, respeak `@claude-code-*` | `<same>@agentik` | unchanged |
| `claude-code-agents@claude-code-agents` | `agents@agentik` | `/agents:status` (was `agents-status`), `/agents:delegate-*`, `agents:local-*`, the two skills |

Plugin code calls the dash name, never the front door, so each plugin needs only its own tool: `allowed-tools` becomes `Bash(agentik-<tool> *)`. Until r2, shims try the new name first, then the old.

### §5.2 The `agentik` marketplace

- **Entries.** `.claude-plugin/marketplace.json`, named `agentik`, lists five entries `{"source":"git-subdir","url":"https://github.com/agentik-dev/agentik-<tool>.git","path":"plugin"}` with versions, checked by `scripts/marketplace-check`.
- **Public.** `claude plugin marketplace add agentik-dev/agentik-commons`; `ref` pins come with r2's tags.
- **The owner's machine (D1).** `make local-marketplace` writes the same file with `file://` urls into `~/.local/share/agentik/marketplace/`, so the IDs match.
- **Per-repo files go.** Each repo's `marketplace.json` is deleted, since two install paths would double the hooks.

### §5.3 Old namespaces

Sessions started before the switch keep theirs. Consumer packets rewrite the live briefs and packets, in-flight ones first. Records are never rewritten.

## §6 The live-file inventory

### §6.1 Live files, classes, the check

**Live** means tracked and outside `design/`, `bugs/`, `history/`, `NICE_TO_HAVE.md` and `CHANGELOG*`. Two exceptions are live because a start line reads them: `history/sessions/PROMPT-*` and `BRIEF-*`, and each running chain's newest charter.

The classes, where a test takes its subject's class:

- **(a)** cosmetic text;
- **(b)** a typed name (CLI, plugin, marketplace, slash command, install line);
- **(c)** a load-bearing path or key (§6.3).

**Declared exceptions**, each a `.hygiene-allow` row:

- the alias lines, the fallback constants and the guards' old spellings;
- hygiene's own patterns, and the `test_readme` reject lists in decisions and respeak;
- strings not ours: Claude Code's `x-claude-code-*` headers (agents `bin/agentroute`, `tests/test-agentroute.py`), respeak's `claude-code-integration` (3 files), relay's redacted `internal/stream/testdata/real.jsonl`.

**The check** is a new group, `renamed`, in the canonical `scripts/hygiene`. It scans the live files, briefs included. Its patterns are `(?<![\w-])claude-code-(session|decisions|respeak|agents)`, `agent-relay`, `claude-session`, `claude-(api-agent|local|fanout|costs|agents)\b`, `\blocalrig\b`, `\bagentroute\b`, and the backticked `` `relay <verb> `` and `` `decisions <verb> ``.

**Exit codes, for the whole scanner, per §7.2.** 0 means no hit outside the allowlist. 1 means a hit (a check said no). 2 means usage, git failing, or `--require-private` without a readable list. The commons packet swaps today's 1 and 2, and each copy's `test_hygiene` changes at its next sync.

### §6.2 Per repo

Each row heading gives `claude-code-` files / files with any old name. `mkt.json` is `.claude-plugin/marketplace.json`; `plugin.json` is under `plugin/.claude-plugin/`.

| repo | (a) | (b) | (c) | tests that follow |
|---|---|---|---|---|
| relay 6/52 | `assets/icon.svg`, `DECISIONS.md`, `internal/relay/types.go`, `internal/hooks/hooks.go` comments | `mkt.json`, `plugin.json`, `README.md`, `internal/prompt/rules-orchestrator.txt`, `cmd/relay/verify.go` | `internal/effects/config.go:47–50` (c1 c3 c4 c6); `effects.go:188`, `hooks/hooks.go:172`, `night/pidfile.go:94` (c2); `hooks/guards.go` (c12); `cmd/relay/` (c14); `plugin/hooks/run` (c11) | 31 `*_test.go`, 6 `internal/packet/testdata/*.md` |
| session 20/61 | messages in `claude_session/{admission,measure,mod,models,rules,sessionconfig,hooks}.py`; `RUNBOOK.md` | `mkt.json`, `pyproject.toml`, `cli.py`, `chain.py`, `plugin/commands/*.md` ×6, `plugin/skills/session/SKILL.md`, `scripts/readme-render`, `README.md` | `config.py:13` (c1); `resolver.py:63,241` (c4 c5); `doctor.py:21,36–40,384` (c6 c7); `launch.py:29` (c13); `profiles.yaml:51,72` (c6); `install-wrapper.sh`, `Makefile` (c1 c8); `plugin/hooks/{run,session.ts}` (c11) | 25 in `tests/` (a fixture folder is c4); 2 `*.test.ts` |
| decisions 12/18 + 4 briefs | `CLAUDE.md`, `tests/fixtures/backlog/*` | `mkt.json`, `README.md`, `pyproject.toml`; 4 `history/sessions/PROMPT-*` | `src/decisions/doctor.py:37,213` (c7 c1); `.python-version`, `Makefile:99,123` (c10); `.gitignore` (c4) | `test_doctor.py`, `test_hermetic.py`, `test_readme.py` |
| respeak 18/20 | `CLAUDE.md`, `plugin/docs/config-layers.md` | `mkt.json`, `README.md`, `Makefile:84–95` | `plugin/scripts/respeak-doctor.sh` (c7); `respeak-config.py:140`, `respeak-gate.sh` (c1); `.python-version`, `Makefile:6` (c10) | `tests/test_{check,doctor,install}.sh`, `test_provider_layer.py` |
| agents 21/22 | `bin/{claude-local,localrig,queue-mvp}` | `mkt.json`, `plugin.json`, `plugin/agents/local-*.md` ×5, `plugin/commands/delegate-local.md`, `plugin/skills/*/SKILL.md` ×2, `README.md`, `Makefile:84` | `bin/claude-agents:104` (c1); `bin/{localrig,agentroute,claude-api-agent,claude-costs}` (c17–c19); `.hygiene-allow` (c15) | `tests/test-status.py` |
| agentik-dev-github 1/1 | — | `profile/README.md` | — | — |
| consumer repos | see the private notes | 27 briefs, 3 charters, CLAUDE.md, a template, the ledger | config (c4 c6) | — |

The remaining hits are exceptions: `scripts/{hygiene,doclint,readme-render*}`, `test_{doclint,hygiene}`, the reject lists, the third-party strings, and the eight agents names (aliases).

### §6.3 (c): migrations and fallbacks

These rules apply to every row:

- Only names change, never formats.
- Readers take the new path, else the old; that is the fallback unless a row says otherwise. Writers write where the reader resolved, so until a folder moves, old and new code share the old one.
- Folders move only in the cold window (§8.5), by `mv` plus a symlink back, in one Bash call.
- r2 removes the symlinks and the fallbacks.

| # | old → new | migration | fallback, if not the default |
|---|---|---|---|
| c1 | `~/.local/state/claude-code-session/` → `…/agentik-session/` (five readers) | cold window | |
| c2 | `~/.local/state/agent-relay/` → `…/agentik-relay/` (ledger, pid, session hooks) | cold window | |
| c3 | `~/.config/agent-relay/` → `~/.config/agentik/relay/` | none (absent on the owner's machine) | |
| c4 | `.claude/claude-code-session/` → `.claude/agentik/` in each repo | `git mv` in each consumer packet | doctor flags the old |
| c5 | `~/.claude/claude-code-session/profiles.yaml` → `~/.claude/agentik/` | none (absent on the owner's machine) | |
| c6 | config section `agent-relay` → `relay` | consumers rename the key | with both present, `relay` wins with a warning |
| c7 | plugin IDs → `<p>@agentik` | the switch | doctors accept both and warn |
| c8 | `~/.local/share/claude-session/` → `…/agentik-session/` | new trees go there | old trees stay while used |
| c9 | dists `claude-code-{session,decisions}` → `agentik-*` | `uv tool uninstall claude-code-decisions` | the `decisions` entry point |
| c10 | venvs `claude-code-{decisions,respeak}` → `agentik-*` | `make venv` | `pyenv prefix new \|\| old` |
| c11 | CLI names in shims, `session.ts`, `allowed-tools` | each CLI goes in before its plugin | the alias |
| c12 | guards on `claude-session`, `relay`, `cmd/relay` | match all three spellings | the old spelling stays denied |
| c13 | `launch.py`'s plugin search names `claude-code-{respeak,agents}` | the new names | the old folder links |
| c17 | `~/.local/state/agentroute/` → `…/agentik-agents/route/` (localrig pids, keys, logs) | cold window, after `localrig down` | `AGENTROUTE_STATE_DIR` still wins |
| c18 | `~/.local/state/claude-api-agent/` → `…/agentik-agents/api/` (usage log) | cold window | `CLAUDE_API_AGENT_LOG` still wins |
| c19 | `~/.config/agentroute/` → `~/.config/agentik/agents/route/` | cold window, router stopped | |

c14–c16: `cmd/relay` and the `.hygiene-allow` rows are renamed; the plugin data folders are empty. Unchanged (nobody types them): `CLAUDE_SESSION_*`, `RELAY_*`, the module `claude_session`, the Go module path.

## §7 agentik-commons

### §7.1 Layout

```
bin/agentik tests/  scripts/{hygiene,bounded,sync,marketplace-check}  .claude-plugin/marketplace.json
GUIDE.md docs/sibling.md design/ README.md NICE_TO_HAVE.md LICENSE Makefile .hygiene-allow
```

### §7.2 The consistency guide

`GUIDE.md` takes over agentik-session's `design/conventions.md` (§1–§9, renamed), which keeps a pointer. It adds:

| part | content |
|---|---|
| naming | `agentik-<tool>` for the repo, executable, dist, venv and state folder; plugin `<tool>@agentik`; config in `~/.config/agentik/<tool>/` and `.claude/agentik/config.yaml`; new env vars `AGENTIK_*` |
| verbs | Words or verb-noun (`setup-key`), never a flag as a verb. `doctor` checks the machine, `status` reads once, `report` writes markdown, `run` drives, `hook` is internal. Every tool has `--help`, `--version` and `doctor`; reads take `--json`. |
| exit codes | Exit codes report the task, not the content. 0: done. 1: a check said no. 2: usage or a failed precondition. 3: not installed. |
| docs | READMEs show `agentik <tool> <verb>`; code uses the dash name |
| README shape | The docs-r1 order: Why it exists, What it does, Does it work?, Install, Commands and skills, the tool's own sections, Design of record, Tests, Conventions shared with the sibling plugins, What can go wrong, Status, Layout, License. The sibling paragraph is decisions' wording, kept in `docs/sibling.md`. |
| install, hygiene | BINDIR is `~/.local/bin`; each CLI goes in before its plugin. Groups: home, lan, sibling, secret, email, renamed; the private list stays outside the repos. |

### §7.3 Shared code: now and later

- **Now:** `scripts/hygiene` (its canonical copy moves here from session, gains `renamed` and takes §7.2's exit codes), `scripts/bounded` and `scripts/agentik`.
- **Later:** `scripts/doclint` becomes one copy in r2. `scripts/py`, the readme renderers and the doctors' plugin-ID read get their own record.
- **How repos get them:** a vendored copy, its sha256 pinned in the Makefile and checked by `make check`; `scripts/sync` refreshes it in a packet. A Python library could not serve the Go repo.

## §8 The rollout

### §8.0 Step 0: the ledger amendment

Before any packet, the owner's portfolio ledger amends the four entries that name the old surface:

- **plugin conventions:** one guide and one `agentik` marketplace, both in agentik-commons, and no per-repo marketplace;
- **the launcher:** `agentik session run`;
- **the decisions verbs:** `agentik decisions …`;
- **the relay entry:** its repo is agentik-relay.

The exit-code rule needs no change. The exact text and the paste line for the ledger's session are in the private notes. Step 0 precedes every packet.

### §8.1 Order

0. Step 0 (§8.0).
1. `agentik-r1-commons`, which has no live effect.
2. The tool and profile packets, in parallel, reviewed on their branches. The tool branches merge only in the switch: four of the old marketplaces read the checkouts and one reads the public respeak repo, so a merge before the swap removes a live manifest.
3. The switch (§8.3).
4. The consumer packets. Until they land, the aliases carry the old callers.
5. The cold window (§8.5).
6. r2 (§8.6).

### §8.2 Packets

| packet | scope | the test that fails before |
|---|---|---|
| agentik-r1-commons | §3, §5.2, §6.1, §7 | `agentik nosuch` exits 3; a fake `agentik-x` is listed and passes argv and exit through; a `renamed` hit exits 1 |
| agentik-r1-decisions | §4.1; c1 c7 c9 c10 | `agentik-decisions --version` runs |
| agentik-r1-agents | the dispatcher; plugin `agents`; c1 c17–c19 | `agentik-agents setup-key` reaches a stub `claude-api-agent --setup-key` |
| agentik-r1-respeak | c1 c7 c10 | `test_doctor.sh` reports `respeak@agentik` |
| agentik-r1-session | §4.1; c1 c4–c8 c11 c13; start lines; `test_readme` | install writes `agentik-session` and the old link |
| agentik-r1-relay | §4.1; c2–c4 c6 c11 c12; plugin `relay`; resume lines | a row is denied `agentik relay run` |
| agentik-r1-profile | the org profile README | `renamed` counts 0 |
| one per consumer repo | its rows in the private notes, by its own session | `renamed` counts 0 over its live files |

Each packet needs step 0 first, clears its whole §6.2 row, vendors `scripts/{agentik,hygiene,bounded}`, deletes its `marketplace.json`, and has `renamed` 0 as an acceptance line.

### §8.3 The switch

**Preconditions:** step 0 entered; tool branches reviewed and merge-ready; no relay night (`run`, `gate`, `plan`), helper or other install. Sessions and launchers may run (§8.4).

0. **Merge.** Merge the five tool branches; push none before step 4 passes.
1. **CLIs first.** Install decisions (`uv tool uninstall claude-code-decisions && make install`), then agents, session and relay. No folder moves yet.
2. **Local marketplace.** Run `make local-marketplace`, then `claude plugin marketplace add ~/.local/share/agentik/marketplace`.
3. **Swap each plugin.** `claude plugin install <p>@agentik`, then `claude plugin disable <old id>`. Old IDs are uninstalled only in r2.
4. **Verify.** `claude plugin list`, then A1–A4 (§9).
5. **Freeze.** The owner's machine mirror freezes the new settings.

### §8.4 What keeps running through the switch

| running | keeps | needs until it exits |
|---|---|---|
| a launcher from the pre-move checkout path | its old interpreter, tree, state path | the old checkout-folder link |
| a launcher from the current checkout | its tree and the old state path | its tree (prune keeps it) |
| a successor started after the switch | the new plugins | `agentik-session` (step 1) |
| a session started before the switch | its old plugins; disabled IDs keep their cache | the aliases, silent in hooks |
| a relay child | `RELAY_BIN`, absolute | no install during a night |

### §8.5 The cold window

**Preconditions,** checked by `ps` before and after: no `claude`, no launcher (each chain stopped at a checkpoint), no night.

1. Move c1, c2 and c17–c19.
2. The owner restarts each chain with `agentik session run …`.
3. A compat link to an old checkout folder goes once no process command line and no live file names it, at the latest in r2.

### §8.6 r2: the aliases end (on or after 2026-12-31)

In one quiet window, once every `renamed` count is 0:

- Remove the old names, the symlinks, the fallbacks and the compat links.
- Uninstall the old IDs and their marketplaces.
- Move agents' scripts to `libexec/`.
- Re-render each scope.
- Bump each tool's major version: the resolved file loses `agent-relay`.

## §9 Acceptance and proofs

| id | line |
|---|---|
| A1 | `agentik` lists four tools; `agentik nosuch` exits 3 |
| A2 | `agentik session doctor`, `relay status`, `decisions show 5` and `agents key-status` match their old forms |
| A3 | Old names work: one note on a terminal, nothing new in hooks or pipes |
| A4 | Five `@agentik` plugins are enabled and the five old ones disabled |
| A5 | A new session has the session band and the push guard; `doctor` is green |
| A6 | A row is denied `agentik relay run`, `agentik-relay run`, `relay run`, `agentik session start` and `claude-session start` |
| A7 | `renamed` counts 0 over every repo's live files, briefs included |
| A8 | After the cold window, the old state paths are symlinks and the file counts match |
| A9 | Naming rule (one function per repo, the name says its layer): commons is the tools' shared ground and builds no tool |
| P1 | A `file://` `git-subdir` entry installs and its hooks run, in a scratch `CLAUDE_CONFIG_DIR`. If it fails, D1 falls back to the public marketplace. |
| P2 | A disabled plugin's cache and hooks survive for a session that loaded it. If not, the switch waits for older sessions to end. |
| P3 | After the uninstall, `uv tool install` gives both `agentik-decisions` and `decisions` |

Each reversible choice above is one row.

## §10 Decided

Decided under the owner's word of 2026-10-13, as reversible choices the owner may reverse.

- **D1.** The owner's machine installs from a local `agentik` marketplace built from each checkout's committed main, with the public IDs.
- **D2.** relay and agents take short plugin names in the switch (`/relay:status`, `relay:builder`).
- **D3.** Every tool's install also installs the `agentik` front door from its vendored copy.
- **D4.** respeak gets no command in r1; a later packet adds `doctor`, `config`, `render`.
