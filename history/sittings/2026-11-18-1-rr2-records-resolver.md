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
| C R8: the copy (byte-equal test), `records` (verb 14), the doctor row in `do_doctor`'s read only, 15 catalogue ids, suite 0.7.35, the kept ids re-pinned (46); the Home fixture and three in-process doctor runs stand in a temp folder; 160 tests of the touched files OK | done |
| D R9: GUIDE §12, the key, the states, the checks, the verb and the row | done |
| G hygiene over the branch; `make check` through the gate | open |

## Next act

G: `make voice` then `make check` through the gate; commit the sidecar.

## Handover

- decide, owner: the coordinator. Commit 39bd128 holds a made-up address in `tests/test_rr2_records.py` (group `email`, two lines: a fixture's git author and committer, `builder` at `example.invalid`); 4458c4f split it, so the tree scans clean but `--commits main..HEAD` does not. Consumer: the landing's range scan (an allow row, or a squash at landing).
- choice: the records row is read by `doctor` alone, not by `update`'s close on the same read, so update runs no git (`test_ak4a_update` test_7). Consumer: none.
- choice: `resolve` raises `NoRepo` for a folder in no git checkout; the verb exits 2, the doctor gives no row. Consumer: rr3 onward.
- choice: the object carries `schema` first; `why` is a code, each tool's sentence its own. Consumer: the relay's port.
- choice: git runs with the local environment variables dropped (a hook's GIT_DIR). Consumer: none.
- note: one full direct run, 1236 tests, one failure, `test_up2_suite_origin` test_12, a `git clone --bare` hardlink race unrelated to this row.

## Exit

Open.
