# Packet c2: the one line

| item | value |
|---|---|
| from | agentik-hq HANDOFF 17, build 2; `~/code/agentik-hq/design/04-self-contained-plugins.md` §7 item 7, §5, §6 (the marketplace `version` row), §11, §12 F2; hq entry 6 |
| pin | commons main ab5cc97, the `agents` 1.5.1 line (a-s18's landing); worktree `~/code/agentik-commons/.claude/worktrees/c2-suite`, branch `c2-suite`, cut there |
| wall | this repo; read `~/code/agentik-session`, `~/code/agentik-decisions`, `~/code/agentik-agents` at main, never write there (a `git clone` from them into `$T` is a read); no push, `--amend`, rebase, merge, real `make install`, real `install-cli`; `claude` only as granted below; a test never writes under the live `~/.local`, `~/.claude`, `~/.config`; never touch `~/.config/agentik/hooks-follow-launcher`; no relay verb or binary; no `kill`, `pkill` or signal from a script; never a gate verb under a temp HOME |
| `claude`, granted | `claude plugin validate`, and in the probe only `claude plugin marketplace add/update/list` and `claude plugin install/update/list`, each run as `env -i HOME=$T PATH=/usr/bin:/bin:<claude's dir> DISABLE_AUTOUPDATER=1 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 claude plugin ...` with `$T` under your scratchpad. Never a prompt, `-p`, a session, or any verb that reaches a model; never with the live HOME or a `CLAUDE_CONFIG_DIR` |
| may touch | `plugins/suite/` (new), `.claude-plugin/marketplace.json`, `scripts/marketplace-check`, `scripts/marketplace-versions`, `scripts/local-marketplace`, `scripts/suite-probe` (new), `Makefile` only if a check needs it, `tests/`, `README.md`, `GUIDE.md` lines that count the plugins, `NICE_TO_HAVE.md`, this packet as the repo's packet file, a charter under `history/sittings/` |
| acceptance | §2's acts; `make check` green |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c "make check > <scratch log> 2>&1"`, then `agentik session gate wait <id>` in one background Bash, last. It exits 0 whatever the job's code: read the code from its line |
| budget | One commit per act. **Stop at 120k context or 90 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

Read, by sections only: design/04 §5, §6, §7 item 7, §11; this repo's GUIDE §9, §10; `scripts/marketplace-check`, `marketplace-versions`, `local-marketplace` and their tests; each tool's `tests/test_bare_machine.py` at main for the commands it runs. Claude Code's plugin docs for the `dependencies` field of `plugin.json` and for `git-subdir` sources (the claude-code-guide agent may answer; cite what you read).

hq entry 6, verbatim in its first sentence: "The Claude Code plugin repos share one consistency guide, GUIDE.md in agentik-commons, which also holds their canonical shared scripts and the one marketplace, `agentik`, listing every plugin as `<tool>@agentik`; a plugin repo keeps no marketplace file of its own."

## 1. What this is

A fresh Mac installs the suite in one line, design/04 §5: `claude plugin marketplace add agentik-dev/agentik-commons && claude plugin install suite@agentik`. `suite` is a manifest-only plugin in commons whose `dependencies` are session, decisions and agents. **Not here:** respeak, relay or the observer in the suite; dropping the marketplace `version` lines (§2 act 5 only records what the probe shows); any tool repo's code.

## 2. Acts and rulings

0. This packet, committed first.
1. **The plugin.** `plugins/suite/.claude-plugin/plugin.json`: `name` `suite`, `version` `0.1.0` (hq's pick, reversible: new and unproven), a one-line description, `dependencies` on session, decisions and agents in the form Claude Code's docs give, and nothing else: no hooks, bin, skills or commands. `claude plugin validate plugins/suite` clean, or each warning named in the charter.
2. **The entry.** A sixth line in `.claude-plugin/marketplace.json`, after agents: `suite`, `{"source": "git-subdir", "url": "https://github.com/agentik-dev/agentik-commons.git", "path": "plugins/suite"}`, its version. If the docs or the probe show `git-subdir` cannot name this repo's own subfolder, a relative `./plugins/suite` source is the fallback; say which in the charter.
3. **The scripts learn it.** `marketplace-check`: the published file holds the five and `suite`, six, suite's url commons' own and its path `plugins/suite`; under `--local`, suite is absent, and present is a problem line. `local-marketplace` omits suite (this Mac installs by name). `marketplace-versions` compares suite's line with `plugins/suite/.claude-plugin/plugin.json` in this repo. If `plugin-version-check` runs over this repo, it covers `plugins/suite`. Tests for each: the six pass; suite missing, suite's url wrong, suite's path wrong, suite under `--local`, suite's version drifted each fail on one line. `make check` green.
4. **The probe**, `scripts/suite-probe`, run by hand, never by `make check`. Under `$T`: clone this worktree's HEAD and the three tools' mains into `$T/code/`; build `$T/market/.claude-plugin/marketplace.json` from this branch's file with `file://$T/code/agentik-<name>` urls and suite's to the commons clone; then `marketplace add $T/market`, `install suite@agentik`. It prints, and the charter records: the three tools and suite in `$T/.claude/installed_plugins.json` (or where Claude Code writes it), each at its main's version, agents 1.5.1; exec bits on each installed `hooks/run` and `bin/*`; and each tool's bare-machine commands, as its `tests/test_bare_machine.py` runs them, against the installed copy, under env exactly `HOME=$T`, `PATH=/usr/bin:/bin`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, exits as those tests expect. Nothing reaches a model server.
5. **The version question** (design/04 §6). In the probe, bump one tool's `plugin.json` in its `$T` clone and commit there; `marketplace update agentik`, `update <tool>@agentik`, once with the entry's `version` left at the old value and once with the entry's `version` removed. Record whether `update` installs the bump in each case. Change nothing on the strength of it: the drop, if the probe says so, is a later packet.
6. **Docs.** README's first lines: §5's install line, the suite named, and the "no plugin of its own" sentence corrected to a manifest-only plugin; GUIDE lines that count five plugins in the marketplace, if any, say six. Any `marketplace-check` docstring that says five says six.

## 3. The stop

Stop and report, committing what is there, on: the probe showing `install suite@agentik` does not install the three dependencies (design/04 §5's fallback is a `for` over the three names, hq's to take); Claude Code refusing a dependency across one marketplace; an installed copy losing an exec bit or `plugin/lib`; a check that needs a tool repo changed. A stop is a result.

## 4. Report (at most twelve lines)

The branch and sha; each gate's id and its code from the line; each act's result; the suite's test counts; the probe's commands, `installed_plugins.json`'s three versions, the exec bits, the bare commands' exits; act 5's two answers; anything decided or left over, and if you stopped, the exact resume line.
