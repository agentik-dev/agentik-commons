# Packet c5: the marketplace lines for agents 1.5.3 and session alpha.45; NICE n4

| item | value |
|---|---|
| from | hq CLAUDE.md flow step 8 (a plugin bumps `plugin.json` and the marketplace line in commons); a-s19 landed agents 5b717af at 1.5.3, s52 landed session 399e6de at 2.0.0-alpha.45, both installed 2026-11-01; commons NICE n4 (hq's decision: rides commons' next packet) |
| pin | commons main eff4fd5; worktree `~/code/agentik-commons/.claude/worktrees/c5-lines`, branch `c5-lines`, cut there |
| wall, verify | c3's packet rows (`design/packets/c3-recordlint.md`), unchanged |
| may touch | `.claude-plugin/marketplace.json` (two `version` values only), `README.md` (its `make check` line), `NICE_TO_HAVE.md` (n4's row leaves), this packet as `design/packets/c5-lines.md`, a charter under `history/sittings/` |
| budget | One commit per act. **Stop at 40k context or 25 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

## Acts

0. This packet, committed first.
1. **The lines.** `.claude-plugin/marketplace.json`: `session`'s `version` to `2.0.0-alpha.45` (line 15) and `agents`' to `1.5.3` (line 55), matching `~/code/agentik-session/plugin/.claude-plugin/plugin.json` and `~/code/agentik-agents/plugin/.claude-plugin/plugin.json` at main; nothing else in the file. `scripts/marketplace-versions` green against the siblings.
2. **n4.** `README.md:34`'s `make check` line names recordlint, which check runs after hygiene; n4's row leaves `NICE_TO_HAVE.md` in that commit. recordlint green.
3. The gate, last; read the code from its line.

## Report (at most five lines)

The sha; each act's commit; the gate's id and its code from its line; `marketplace-versions`' line.
