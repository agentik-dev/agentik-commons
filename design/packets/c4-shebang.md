# Packet c4: recordlint's shebang to hq entry 6; design/04 §6's row

| item | value |
|---|---|
| from | a-s19's refuter round 1, observation (a): `scripts/recordlint` takes `#!/usr/bin/python3`, against hq entry 6 ("A repo's own dev scripts and gates keep an `env python3` shebang"), where every other commons gate (`hygiene`, `bounded`, `plugin-version-check`, ...) takes `#!/usr/bin/env python3`; h1's refuter F1 (design/04 §6's S4 has no NICE row) |
| pin | commons main 05bc434; worktree `~/code/agentik-commons/.claude/worktrees/c4-shebang`, branch `c4-shebang`, cut there |
| wall, verify | c3's packet rows (`design/packets/c3-recordlint.md`), unchanged |
| may touch | `scripts/recordlint` (line 1 only), `tests/test_recordlint.py`, `NICE_TO_HAVE.md`, this packet as `design/packets/c4-shebang.md`, a charter under `history/sittings/` |
| budget | One commit per act. **Stop at 50k context or 30 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

## Acts

0. This packet, committed first.
1. **The shebang.** `scripts/recordlint` line 1 becomes `#!/usr/bin/env python3`; `tests/test_recordlint.py:69` pins that line; the 3.9-floor run stays explicit (`/usr/bin/python3 scripts/recordlint ...` where a test runs the floor). Nothing else in the script changes.
2. **The row.** NICE `n7`, `S4`, area `` `.claude-plugin/marketplace.json` ``: design/04 §6's drop of the marketplace `version` lines is not built (a packet when a commons change rides); evidence: hq `design/04-self-contained-plugins.md` §6, hq `history/handoff-done.md` item 17; from: 2026-11-01, h1's refuter F1. recordlint green.
3. The gate, last; read the code from its line.

## Report (at most six lines)

The sha; each act's commit; the new sha256 of `scripts/recordlint`; the gate's id and its code from its line; the suite's counts.
