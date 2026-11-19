# Sitting 2026-11-19-1-sm6-commons-small: row sm6-commons-small, a small change under hq entry 17 (builder)

| item | value |
|---|---|
| goal | NICE n76 (the suite's settings read refuses a file that is not regular) and n197 (one word rule for `config.asks` and `doctor._closes`), one commit each, each row leaving NICE_TO_HAVE.md in its commit |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | main ca83060; nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; no packet (entry 17); no version line by hand |
| verify | `tests/test_sm6_commons_small.py` and the touched tests directly; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| n76 settings.read through `read_regular`: a FIFO, a folder, bytes not UTF-8 a Fault at once; 2 tests, 1 red at ca83060 (a 10 s timeout), 2 OK; sc6, sc7, fk1, ak3d, su1 70 OK | done |
| n197 `doctor.asks`, the one rule of `config.asks` and `_closes`: quotes stripped, case folded, `--assume-yes`, a `-` cluster holding `y`; 1 test, red at 99b2214, OK; ak9b, sc10, sc5, ic1 74 OK | done |
| V `make check` through the gate | open |

## Next act

V, the gate.

## Handover

- choice: n197's rulings: `--YES` and `REMOVE` count (case folded), `--assume-yes` counts; a false hit only moves a remedy off `next:`. Consumer: none.
- choice: n76 keeps the Fault's words, `a file that cannot be read`, for a path that is no regular file. Consumer: none.

## Exit

Open.
