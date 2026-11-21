# Sitting 2026-11-20-6-rc0-records-cut: row rc0-records-cut, review 2's round (builder)

| item | value |
|---|---|
| goal | review 2's ruling: F1 to F4 one proof after the copy (the holder's own `git add --dry-run` takes every copy, else the copies go and the clone is untouched); F5 remotes by host and path; L3 `.hygiene-allow` as git compares it; L1, L2, L4 NICE rows; the words; the phase 2 only if rr7-way-in is on main |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | branch tip 897a099 (checked head fbf61b4; main f1135d5); nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; the script only on scratch fixtures |
| verify | `python3 -m unittest tests.test_records_cut` directly; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| P the proof (F1 to F4) | done: after the copy and its sums, before the clone changes, each copy's folder's top is the holder's and `git add --dry-run -- repos/<name>` exits 0 naming each copy, else the copies are taken back and it refuses (exit 2); before the copy, the nearest folder's top, a submodule at or above the destination and the sparse rules (`check-rules`) are refused; `HolderTakesTest`, 3 tests over review 2's 5 fixtures |
| R the remotes (F5) | done: each fetch and push URL keyed as (host, path), the scheme, a user, a port, the short `host:path` form, a trailing `/` and `.git` dropped, both case-folded; a local one by its real path; `RemoteSpellingTest`, review 2's three spellings and build 2's |
| A `.hygiene-allow` (L3) | done: HEAD's where `git diff --quiet HEAD` finds no change and `git hash-object --path` is HEAD's blob (so a flag-hidden edit is still refused); `LineEndTest`, an `eol=crlf` attribute and `core.autocrlf` |
| U the riding fix (the coordinator's, 2026-11-20) | done: `test_up2_suite_origin` test 12's bare clone takes `--no-hardlinks`; the packet's may touch names the file |
| N the NICE rows (L1, L2, L4) | done: n269 to n271 in "From row rc0-records-cut (review 2)"; n203, n205 to n208, the next oldest S4, to the overflow for the bound; recordlint held, 65 rows |
| W the packet, the header, GUIDE §12 | done: the header and GUIDE §12 say the proof, the new refusals, the remotes and `.hygiene-allow` as built; the packet gains R4b and acceptance 11 |
| P2 the phase 2, if rr7-way-in is on main | not done: main's last eight (head f1135d5) show no rr7-way-in merge once the fixes were committed; a later act |
| V the probes, hygiene, the gate | the new tests red at fbf61b4 (a scratch archive, 21 subtests), `tests.test_records_cut` 15 OK at head; review 2's probes on my own scratch fixtures: R1, R2, G3, G4, SP and F5's spellings exit 2, the clone unchanged, the holder holding nothing made (two folder mtimes move); L3 and a plain move exit 0; hygiene tree exit 0, `main..HEAD` exit 1 on 169e93b alone (handover); the gate queued on this head |

## Next act

The phase 2 once rr7-way-in is on main: merge main; keep main's NICE rows and overflow; renumber n261, n262 and n263 to n271 after main's highest, in the packet and the record; more old S4 rows to the overflow if the bound needs.

## Handover

- decide, owner: coordinator. F5's test (169e93b) wrote ssh and https URLs with a user (`git@`, `user@` at `forge.invalid`), which the email group reads; the tree now splits them (hygiene's tree scan exit 0), the commit scan still counts 169e93b (6 hits). A row `tests/test_records_cut.py: email`, as fk1-sources' and rr2's, would hold it. Consumer: the landing.
- decide, owner: coordinator. NICE n262 is the up2 flake the riding fix mends; left open, for the landing to close. Consumer: the landing.

## Exit

Review 2's round built (F1 to F5, L3, the NICE rows, the words) and the coordinator's riding fix; no phase 2, rr7-way-in not on main; `make check` queued once on this head, its line in the row's record.
