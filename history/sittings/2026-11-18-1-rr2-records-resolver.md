# Sitting 2026-11-18-1-rr2-records-resolver: row rr2-records-resolver, its first build (builder)

| item | value |
|---|---|
| goal | one stdlib resolver, `scripts/agentik_records.py`, answers where a repo's working records are (`own`, `out`, `unset`, `broken`); a table of cases proves it; `scripts/sync` places it; the suite gains `agentik records` and one doctor row; GUIDE §12 says it |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | main 4aa4347 (suite 0.7.34); branch `rr2-records-resolver`; nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; no model started; sync only on temp trees; no test reads a real repo's git config or the live home |
| verify | the new and touched test files directly; `make check` once, last, through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` |

## Done-ness

| act | done-ness |
|---|---|
| P the packet and this charter | done |
| A R1 to R6: the resolver, `tests/records_cases.json` (28 cases), `tests/test_rr2_records.py`; `-k test_cases` red with the file moved aside (1 error), 4 OK under python3 and /usr/bin/python3 | done |
| B R7: `scripts/sync` places `plugin/lib/agentik_records.py`, listed and named; `tests/test_sync.py`'s placed set; `test_rr2_records.SyncTest` (the copy runs under `-I`); test_sync and test_ak10b_term 22 OK; acceptance 2 by `cmp` with the pin's no-lib sums (61746a92); the README's rows | done |
| C R8: the suite's copy, `records`, the doctor row, the catalogue, the voice sidecar, the version | open |
| D R9: GUIDE §12 | open |
| G hygiene over the branch; `make check` through the gate | open |

## Next act

C: the suite's copy, `records` and the doctor row.

## Handover

None yet.

## Exit

Open.
