# Packet su6-rows-part: `agentik status` shows the rows in flight and counts what waits on the owner

| item | value |
|---|---|
| from | agentik-hq's brief su6-rows-part of 2026-11-15, R1 to R6; hq design/18 items 10 and 11 (§12's su6 row); level S3 |
| pin | main at abb9b36 (suite 0.7.18); worktree `.claude/worktrees/su6-rows-part`, branch `su6-rows-part`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; the three reads run by hand only read-only; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/status_read.py`; `plugins/suite/lib/agentik_suite/status_screen.py`; `plugins/suite/lib/fallback.json` (one `status` read more in the `session` and `decisions` rows); `plugins/suite/lib/agentik_suite/messages.md` (new ids at the end of `## Status`); `design/voice/checked.sha256`; `plugins/suite/.claude-plugin/plugin.json` (the version, alone); `tests/test_su6_rows_part.py` (new); `tests/fixtures/su6/*` (new); `tests/fixtures/su2/read/e2e.json` and `e2e.piped.txt` (the two parts and the charter read); `tests/test_su2_read.py` (test_8's table and counts); `tests/test_su2_join.py` (`slow_row`, J-5's part list); this packet; `history/sittings/2026-11-15-4.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | a to f below, each a test of `tests/test_su6_rows_part.py`; the su2 tests OK; both hygiene scans 0; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The owner's words

What changes for a person: today `agentik status` ends `not read  what waits on the owner, the rows in flight`; after this row it has a part for the rows in flight (each row's word and next step, and the gate's newest result for its worktree) and a count of what waits on the owner, from the two places those waits live.

## 2. At the pin

Measured at abb9b36: the object's `not_read` is always `["owner", "rows"]` (`status_read.NOT_READ`), and the screen's last line reads `not read  what waits on the owner, the rows in flight`. Five reads in the fallback table (`gate`, `unattended`, `run`, `backlog`, `sessions`). `python3 -m unittest` of the six su1 and su2 modules: 91 tests OK. Read by hand, read-only, in the hq: `agentik decisions rows --json` took 3.8 s for 38 rows (`agentik.rows/1`: `rows`, each `row`, `level`, `state`, `next` {`text`, `command`}, `worktree`; closed rows are not listed); `agentik session gate status --repo <worktree> --json` 0.15 s (`done` newest first); `agentik session charter show --json <checkout>` 0.06 s (`repos`, each `waits`, the Waits part's lines); `backlog --json`'s step `state` is {`cell`, `word`, `rest`, `on`, `n`, `text`}.

## 3. Rulings (the brief's, in short)

- R1 the rows part: the open rows of `rows --json` run for the hq `covers` found, one line each (row, level, state, next) and, for a row with a worktree, the gate's newest result for that path, the calls started together once the rows read answers. Closed and done rows are not drawn; past the cap the part keeps its first lines and says how many more; `--json` carries every row read.
- R2 the owner's count: one line, the `waits` lines of `charter show --json` over the backlog's checkouts, and the build order steps whose `state` is `waiting` on `the owner` or `owner <n>`; a half not read says `not counted`.
- R3 each leaves `not_read` once its read answers; a read that fails or passes its wall is said in its part, as the other sources are. R4 only the three verbs' `--json`; a tool not on PATH is that part's not read.
- R5 the tests a to f; R6 the check, the voice, the version alone and last under `plugins/`.

## 4. Interfaces

- `fallback.json`: `decisions` gains `{"name": "rows", "argv": ["rows", "--json"], "wall_s": 6}`, `session` gains `{"name": "charter", "argv": ["charter", "show", "--json"]}`. The reads run as `rows --json --root <hq>/history/rows` and `charter show --json <checkout>...`; with no hq the rows read is not run, under rule none the charter read is not run (the backlog's rule).
- The object gains two parts after `runs`, in `PARTS` and on the screen: `rows` {`state`, `rows`: each `row`, `repo`, `level`, `state`, `next`, `worktree`, `closed`, `gate` ({`id`, `exit`, `seconds`} or null), `gate_read` (`ok`, `timed out`, `unreadable`, `not installed` or null)} and `owner` {`state`, `hands`, `steps`} (a count, or null for not counted). Each join runs under the gate read's wall.
- The screen does not draw the rows or the owner part where the object does not hold it, so an object of su2's shape draws as it did, its `not_read` saying both.

## 5. Acceptance

| # | line | at the pin |
|---|---|---|
| a | `python3 -m unittest tests.test_su6_rows_part -k test_a_` (two open rows, one with a worktree: two lines, one gate result) | red: no rows part |
| b | `python3 -m unittest tests.test_su6_rows_part -k test_b_` (a closed row is not drawn) | red: no rows part |
| c | `python3 -m unittest tests.test_su6_rows_part -k test_c_` (three `waits` lines and two waiting steps count 3 and 2) | red: no owner part |
| d | `python3 -m unittest tests.test_su6_rows_part -k test_d_` (the rows read failing: `the rows in flight` stays in not read, exit 0) | red: no rows read |
| e | `python3 -m unittest tests.test_su6_rows_part -k test_e_` (`--json` holds both parts) | red: no part |
| f | `python3 -m unittest tests.test_su6_rows_part -k test_f_` (a rows read past its wall reads `timed out`) | red: no rows read |
| g | `python3 -m unittest tests.test_su2_read tests.test_su2_join tests.test_su2_screen` | OK |
| h | `scripts/hygiene` and `scripts/hygiene --require-private --commits main..HEAD` | 0 |

## 6. Choices

The builder's, each reversible, listed in the charter's handover with its consumer.
