# Packet c1: lift

| item | value |
|---|---|
| from | agentik-hq HANDOFF 17, build 2; `~/code/agentik-hq/design/04-self-contained-plugins.md` §7 item 4, §3, §5 step 4, §6; hq entry 6 |
| pin | commons main e2fee16; worktree `~/code/agentik-commons/.claude/worktrees/c1-lift`, branch `c1-lift`, cut |
| wall | this repo; read `~/code/agentik-session` at main d641fd3, never write there; no push, `--amend`, rebase, merge, device, real `make install`, real `install-cli`; `claude` not at all; a test never writes under the live `~/.local`, `~/.claude`, `~/.config/agentik`; **never touch `~/.config/agentik/hooks-follow-launcher`**; no relay verb or binary; no `kill` or `pkill`; never a gate verb under a temp HOME |
| may touch | `scripts/sync`, `scripts/` (new canonical copies), `bin/agentik` only if the copy needs it, `tests/`, `GUIDE.md`, `README.md`, `NICE_TO_HAVE.md`, this packet, a charter under `history/sittings/` |
| acceptance | §2's table; `make check` green |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c "make check > <scratch log>"`, then `agentik session gate wait <id>` in one background Bash, last. It exits 0 whatever the job's code: read the code from its line |
| budget | **Weekly usage is at 97%.** At most 40 tool calls and 80k context; stop there, commit what is done, write the exact resume line. One commit per act. `claude-opus-5-5` |

Read, by sections only: design/04 §7 item 4, §6, §5 step 4; `~/code/agentik-session/plugin/lib/claude_session/install.py` and `prune.py` at d641fd3; `plugin/bin/agentik-session` there; `scripts/sync` and GUIDE §5, §7, §10 here.

## 1. What this is

`install-cli` and the launcher become canonical in commons, so decisions (d25) and agents (a-s18) take the same freeze, launcher and prune without each writing their own. **Not here:** moving decisions or agents; changing session; the hook shim and the switch, which stay session's, the one hook shim to move; the `suite` plugin (c2).

## 2. Rulings and acceptance

1. **The canonical form is generic by name.** The session-specific strings in `install.py` (`SHARE`, `NAME`, the `/session:install-cli` remedy, the state folder's old-name fallback, the `claude-session` link and note, the runner's name) become values the tool passes, read from one small per-tool place the builder names, so a copy stays byte-identical across tools. Session keeps its own module this packet: its adoption is a later packet, recorded in NICE, since the wall forbids writing there and the suite must stay unchanged.
2. **`scripts/sync`** copies the canonical module and launcher into a repo's `plugin/lib/` or `plugin/bin/` when the repo has a `plugin/lib/`, adds `plugin/bin/agentik`, and lists each in `vendored.sha256`. A repo with no `plugin/lib/` gets what it gets today.
3. **GUIDE:** §5 and §10 say what `install-cli` is, the exit codes, the forward-only refresh; entry 6's floor stated as design/04 says.

| what | reads |
|---|---|
| placement | `sync` into a temp git repo with a `plugin/lib/` places the copies and the door; with no `plugin/lib/`, today's set, unchanged byte for byte |
| drift | a one-byte change in a placed copy fails `shasum -c` |
| generic | the canonical module, given a tool name `agentik-x` in a temp HOME under `PATH=/usr/bin:/bin`, freezes, writes a launcher that runs `--version`, prunes, refuses backward; a 3.9 run |
| session unchanged | `git -C ~/code/agentik-session diff --stat` empty, written by nothing here; report a read of whether session's suite would pass against the placed copy, or what it would need |

## 3. The stop

A generic form that cannot stay byte-identical across tools without a design change: stop and report. A stop is a result.

## 4. Report (at most ten lines)

The branch and sha; the gate's id and its code from the line; each row's figure; what session's adoption needs; anything decided or left over.
