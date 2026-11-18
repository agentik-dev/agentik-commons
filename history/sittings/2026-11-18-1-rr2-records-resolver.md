# Sitting 2026-11-18-1-rr2-records-resolver: row rr2-records-resolver, build 1 and the fix of review 1 (builder)

| item | value |
|---|---|
| goal | one stdlib resolver, `scripts/agentik_records.py`, answers where a repo's working records are (`own`, `out`, `unset`, `broken`); a table of cases proves it; `scripts/sync` places it; the suite gains `agentik records` and one doctor row; GUIDE §12 says it. The fix: a set key is never `own` or `unset`; folders compared by the file system; one declaration form |
| budget | Opus; about 90 tool calls a build; past 80% land the act in flight and hand back |
| pin | build 1: main 4aa4347 (suite 0.7.34); the fix: the branch at 56eae2c; nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; no model started; sync only on temp trees; no test reads a real repo's git config or the live home |
| verify | the new and touched test files directly; `make voice` and `make check` once each, last, through the gate queue; `scripts/hygiene --require-private --commits main..HEAD` |

## Done-ness

| act | done-ness |
|---|---|
| P..G build 1: packet, R1 to R9, gate 20261118-060553-2642 exit 0 at 56eae2c | done |
| F1 C1, C2, C5: presence read without `--path` (`unread`, `many`); `repo` the worktree list's first entry; `inside` by same file up the parents and by the shared common git folder; the name by the parent's listing; 43 cases, 15 red at 56eae2c, 43 green | done |
| F2 C3, C4: `records: out` in `.hygiene-allow` alone; GUIDE §12; the broken line names the key and its values; an `out` with no holder says nothing is committed (`doctor.records_why`, `values`); 12 tests of the row OK, 189 of the touched files but the sidecar's | done |
| F3 `make voice`, `make check` through the gate | open |

## Next act

F3: `make voice`, commit the sidecar, then `make check`.

## Handover

- decide, owner: the coordinator. Commit 39bd128 holds a made-up address in `tests/test_rr2_records.py` (group `email`); the allow row of 56eae2c covers it. Consumer: the landing's range scan.
- choice: two config.yaml cases of build 1 change their answer under C3 (declared in config.yaml: `unset` now `own`; a holder's config.yaml: `broken holder` now `out`). Consumer: none.
- choice: the values for the broken line come from `values(start)`, beside `resolve`; the object keeps its seven keys. Consumer: the relay's port.
- choice: a set key moved outside the clone's worktree list (a moved worktree) is caught by its common git folder, with `why` `inside`. Consumer: none.
- choice: the records row is read by `doctor` alone, not by `update`'s close. `resolve` raises `NoRepo` for a folder in no git checkout. git runs with the local environment variables dropped. Consumer: rr3 onward.

## Exit

Open.
