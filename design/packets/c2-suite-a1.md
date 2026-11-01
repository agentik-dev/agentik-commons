# Packet c2, amendment 1: the refuter's round 1

| item | value |
|---|---|
| from | c2's refuter, round 1, FAIL at d5bad18 (hq sitting 2026-11-01-1); the packet and hq's act 7 stand |
| pin | branch `c2-suite` at d5bad18, worktree `~/code/agentik-commons/.claude/worktrees/c2-suite` |
| wall, `claude` grant, verify | the packet's, unchanged |
| may touch | `scripts/suite-probe`, `scripts/marketplace-check`, `tests/`, `GUIDE.md` line 32's paragraph, `NICE_TO_HAVE.md`, this amendment beside the packet, the charter |
| budget | One commit per act. **Stop at 60k context or 40 tool calls.** `claude-opus-5-5` |

## Acts

0. This amendment beside the packet, a line in the charter.
1. **F1 (S3), `scripts/suite-probe:177-203`.** The session part runs only the ten `hooks/run` events and `--version`; act 4 asks for session's bare-machine commands as its `tests/test_bare_machine.py` runs them, and that test also runs `admission record`, `charter open`/`close`, `status`, `doctor`, `report`, `rules`, `budget` and `measure record`. Repro: `grep -nE '"(admission|charter|report|doctor|rules|budget|measure|mod|status)"' scripts/suite-probe` hits only the agents lines. Fix: run each non-gate verb that test runs against the installed copy, with the exits it expects, `admission record`'s ledger line included; `gate` and `install-cli` stay out, said so in the output. Then rerun the probe under the packet's grant; it must print `go`.
2. **F2 (S4, a regression), `scripts/marketplace-check:88`.** `set(names)` raises on a name that is a list or dict (`TypeError: cannot use 'dict' as a set element`), where base printed its problem lines. Fix: build the set over `map(str, names)` as the old code did; a test with `"name": {"x": 1}` gives problem lines and exit 1, no traceback.
3. **F3 (S4), `GUIDE.md:32`.** The line this packet edited still says `dependencies` take `{name, version, marketplace}` with an npm range, while the suite uses bare names. Fix: name both forms Claude Code accepts, and that suite uses bare names because a `^` range does not match a prerelease such as `2.0.0-alpha.43`.
4. **NICE**, one S4 line each: the check does not pin suite's place in the list (the test does); the probe checks files' presence, not content, and reads `route --check` and `doctor` by exit only; `env -i` drops `TMPDIR`, so a tool's temp files may land in `/tmp`, outside `$T`; the published GitHub path is not probed (no network).
5. The gate, last.

## Report (at most six lines)

Head sha; each act's commit; the gate's id and code from its line; the probe's rerun: its last line and the session verbs it ran with their exits.
