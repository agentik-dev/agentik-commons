# Packet sn1-need-notread: setup's plan finds a module where the tool finds it, and `not_read` names every part not read

| item | value |
|---|---|
| from | agentik-hq's brief sn1-need-notread of 2026-11-21, on two findings an advisor reproduced on 2026-11-20; level S3 |
| pin | agentik-commons main 2d96be7, the merge of ak10c5-table-gone; worktree `.claude/worktrees/sn1-need-notread`, branch `sn1-need-notread`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test reads the live home or state; made-up names in fixtures; setup only with `--dry-run` against this Mac |
| may touch | `plugins/suite/lib/agentik_suite/{plan,status_read,status_screen}.py`, `plugins/suite/lib/agentik_suite/messages.md`, `design/voice/checked.sha256`, `plugins/suite/.claude-plugin/plugin.json` (the version), `tests/test_sn1_need_notread.py`, `tests/test_ic2_needs.py`, `tests/test_su6_rows_part.py`, `NICE_TO_HAVE.md` (n281), `history/NICE-overflow.md` (the bound), this packet, `history/sittings/*.md` |
| verify | `python3 -m unittest` of the touched tests directly; `scripts/hygiene --require-private --commits main..HEAD`; `make check` once, last, through the gate queue |
| acceptance | 1 to 6 below |

## 1. The finding

The owner's words (2026-11-20): "continue with the charter", and, giving the sitting six workers, "to accelerate your work". Two readers of one need disagree: setup's plan of respeak warns that PyYAML is missing, since it asks only the `python3` first on PATH (a shim to an interpreter with no PyYAML), while respeak's own launcher walks a list of interpreters and finds one that has it, so its doctor reads ok. And `status --json`'s `not_read` can hold only `owner` and `rows` (`NOT_READ`), so a `sessions` part whose source timed out is left out of the one list a script would trust.

## 2. Rulings

- R1, a module need: met when any interpreter of one ordered tuple, `plan.PYTHONS`, imports it: `python3` first on PATH, then what respeak's launcher tries after it, in its order (`/usr/bin/python3`, `/opt/homebrew/bin/python3`, `/usr/local/bin/python3`, `python3.13`, `python3.12`; a bare name is looked up on PATH). Each probe is under `NEED_WALL` as at the pin; the walk stops at the first that imports, and an interpreter met twice (one real path) is asked once. Where none imports it, `setup.need.module` names the interpreters tried; where none stands, `setup.need.missing` as at the pin. Where a need's word comes from (`needs_of`, `tools.public`, `public.json`) is unchanged.
- R2, `not_read`: every part of `PARTS` but `watchers` whose state is `not read`, in the parts' order; `watchers` is a list of watcher rows and carries no state at the pin. The screen says a part not read once: `_not_read` leaves out a part the screen draws with its own not-read line (a part the object holds as `not read`, or one of the five the object lacks); a part of su6 an object of su2's shape lacks is still said in the foot.
- R3, what stands: the schema's number and every other key; the plan's `Go`; the status screen for a Mac where every part is read, byte for byte; the first screen starts no process it did not start at the pin.

## 3. Interfaces

- `plan.PYTHONS` (the tuple a test patches); `plan.interpreters(search)` giving the `(word, path)` pairs of `PYTHONS` that stand, one a real path; `plan.need_met(need, search, env)` as at the pin.
- Messages: `setup.need.module` gains `{tried}` and says it in place of "the `{program}` first on PATH"; no id added or removed.
- One test changes by ruling: su6's `test_d` read the rows part's `not read` twice, once in its part and once in the foot; R2 says it once.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `-k test_a1`: a stub `python3` first on PATH that fails the import and a later candidate that passes gives no need `warn`; every candidate failing gives the `warn` naming them | the `warn` in both |
| 2 | `-k test_a2`: every candidate hanging, the plan's need read is bounded by the candidates times `NEED_WALL` | one probe, one wall |
| 3 | `-k test_a3`: one `sessions` source timed out: `"sessions"` in `not_read`, and the text screen says it once | absent |
| 4 | `-k test_a4`: every part read: `not_read` is `[]` and the screen equals the pin's | the pin's |
| 5 | not a test: the PyYAML line of `setup session decisions agents observer relay respeak --dry-run`, and `status --json`'s `not_read` beside each part's state, against this Mac at the pin and now | the `warn`; `[]`, owner `partial` |
| 6 | `scripts/hygiene --require-private --commits main..HEAD` exit 0; `make check` through the gate queue | green at 2d96be7 |
