# Packet P1: a plugin's descriptions under 1,024 bytes, measured by one shared script

| item | value |
|---|---|
| from | agentik-hq's brief p1 of 2026-11-11 (`history/sessions/BRIEF-2026-11-11-plugins-p1-description-gate.md`); hq design/09 §1 (F7), §2 (the row "A plugin's descriptions"), §6, §9 step 4; the owner's yes to question 7 of hq design/09 |
| pin | agentik-commons main 8db5ccc; worktree `.claude/worktrees/p1-description-gate`, branch `p1-description-gate` |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no `relay`/`agentik relay` `run`, `plan`, `gate`, `stop`, `kill`, `clean`, `resume`, nothing under `~/.local/state/agent-relay`; no `claude` process; no ledger edited |
| may touch | `scripts/plugin-description-bytes` (new); `scripts/sync`; `tests/test_description_bytes.py` (new); `tests/test_sync.py`; `GUIDE.md` (§1, §5); `README.md` (the scripts table); this packet as `design/packets/p1-description-gate.md`; `history/sittings/*.md` |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id> --strict` in one background Bash; read the job's code from its line |
| acceptance | `python3 -m unittest tests.test_description_bytes tests.test_sync`: OK (8db5ccc: the first module absent, the sync tests that list the copies red); `scripts/plugin-description-bytes` over a checkout of agentik-relay at a3c501d prints `total 1204 of 1024 B` and exits 1, of agentik-agents at c204a3c `total 3195 of 1024 B` and exits 1, of agentik-respeak at ed31c1a `total 574 of 1024 B` and exits 0; `grep -c 'disable-model-invocation: true' GUIDE.md` 1 or more (8db5ccc: 0); `scripts/hygiene` and `scripts/recordlint` exit 0; verify green |
| budget | a commit per group by explicit path, the packet first; `scripts/hygiene` green before every commit. `claude-opus-5-5` |

## 1. What the source says

- **The owner, 2026-11-11.** His yes to question 7 of hq design/09: "The plugins hide the commands only the owner types, under 1,024 B a plugin: yes." And: "A focus should be on avoiding Claude.md bloat".
- **hq design/09 §1, F7.** A skill's or command's description is in context in every main session unless it sets `disable-model-invocation: true`; a general-purpose helper carries the skill list and the agent-type list too; an agent type whose tool list has neither Skill nor Agent carries neither.
- **hq design/09 §2.** "A plugin's descriptions (F7) ... 1,024 B a plugin ... the model itself starts it; a command only the owner types sets `disable-model-invocation: true`." "A plugin repo's `make check` measures its descriptions."
- **hq design/09 §9 step 4.** "agentik-commons' `GUIDE.md` records the two conventions."
- **Nothing measures it today.** `scripts/` holds no reader of a plugin's frontmatter; `scripts/sync:94-98` places five copies.

## 2. Rulings

1. **R1, the measure.** `scripts/plugin-description-bytes [--max BYTES] [PLUGIN_DIR]`, stdlib, `#!/usr/bin/env python3` (GUIDE §7), default `plugin` and 1,024. Counted: the `description` (and a `when_to_use`, which Claude Code shows beside it) of each `skills/*/SKILL.md` and `agents/**/*.md`, and of each `commands/**/*.md`; a command or skill that sets `disable-model-invocation: true` is listed `hidden` and not counted. Bytes are the UTF-8 of the value YAML gives, surrounding whitespace stripped, so a `>` block counts folded, not as written. One line per file, then `total <n> of <max> B`. Exit 0 at or under, 1 over or a counted file with no description, 2 usage.
2. **Shared as the others are.** `scripts/sync` places it at `<repo>/scripts/plugin-description-bytes`, 755, beside `plugin-version-check`, and lists it in `vendored.sha256`; its header, its last line and README's row name it.
3. **R2, the convention.** GUIDE §1 gains a paragraph: the 1,024 B ceiling and its reason in one sentence; a command only the owner types sets `disable-model-invocation: true`; an agent type that needs neither Skill nor Agent lists its tools. §1's vendored line and §5's check list name the script.
4. **Not here.** No plugin repo's descriptions: each takes its own packet p1-description-gate after this lands.

## 3. Tests

`tests/test_description_bytes.py`, a made-up plugin in a temp dir:

| D | test | 8db5ccc |
|---|---|---|
| 1 | a hidden command is listed `hidden` and not counted; a visible one is | red |
| 2 | an agent is counted; a `>` block counts folded; a quoted value counts unquoted; UTF-8 bytes, not characters | red |
| 3 | a counted file with no description: `error:` line naming it, exit 1 | red |
| 4 | over `--max`: exit 1 and a stderr line; at it: exit 0 | red |
| 5 | a skill that sets `disable-model-invocation: true` is hidden; an agent never is | red |
| 6 | usage and a missing directory exit 2 | red |

`tests/test_sync.py`: `COPIES` and the listed names gain the script; the sync line reads `..., plugin-version-check, plugin-description-bytes, vendored.sha256`.

## 4. Interfaces

The plugin repos copy the file and add its sum line to their `scripts/vendored.sha256`, as `sync` would, and run `scripts/plugin-description-bytes plugin` in `make check`.

## 5. Ledger, NICE, forks

Commons has no ledger. Forks ruled here: `when_to_use` counted with its description (Claude Code shows it beside the description; no suite file sets it today); exit 1 for a missing description, since it is content, not usage (the code rule of `plugin-version-check`).

## 6. Report

The head sha, the gate's id and code, D1 to D6, the three totals, choices, leftovers.
