# Sitting 2026-11-20-5-rc0-records-cut: row rc0-records-cut, review 1's round (builder)

| item | value |
|---|---|
| goal | review 1's ruling: F1 to F5, L3, L4, L7 refused before anything is written, a test each (red at 6cf05fa, green after); L1, L2, L5, L6, L8, L9 as NICE rows; the packet and the help true; the phase 2 only if rr7-way-in is on main |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | branch head 6cf05fa (main b4b4cc8); nothing linked from main |
| wall | this worktree; no push, amend, rebase; no bare make; no relay verb; the script only on scratch fixtures |
| verify | `python3 -m unittest tests.test_records_cut` directly; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| F1 a symlink in the destination's path; the destination outside the holder or inside the clone | done: refused in the survey; two cases in `test_each_refusal_alone` |
| F2 a destination path the holder ignores | done: `git check-ignore --no-index` on each destination path; two cases; the stray case now excludes its one file, not `repos/` |
| F3 a record flagged assume-unchanged or skip-worktree | done: the flags refused (`git ls-files -v`: a lowercase tag or `S`), not a compare of bytes; two cases |
| F4 a `.hygiene-allow` that is not HEAD's | done: a working file absent at HEAD, one whose bytes differ from HEAD's, or an absent one the clone ignores, refused; three cases |
| F5, L3 a HEAD behind its upstream; a remote-tracking branch with a record commit | done: `upstream...HEAD` counted both ways; the remote-tracking branches but the upstream and symrefs join the tips; two cases |
| L4 a holder sharing a remote URL with the clone | done: each fetch and push URL compared, a local path by its real path, others case-folded, less a trailing `/` or `.git`; two cases |
| L7 a submodule at or under a record name | done: mode 160000 joins 120000 at, under or above a record name; one case |
| N the NICE rows from review 1 | done: n263 to n268 (L1, L2, L5, L6, L8, L9) in "From row rc0-records-cut (review 1)"; n191 to n194 and n200 to n202, the oldest S4, to `history/NICE-overflow.md` for the 24,576 B bound; recordlint held, 67 rows |
| W the packet, the help, GUIDE §12 | done: the header lists every refusal and says the hooks run; GUIDE §12 the same in its sentence; the packet gains R4a, acceptance 10 and the overflow in may touch |
| V the probes, hygiene, the gate | the 14 new cases red at 6cf05fa (the new test file over a scratch archive of the pin: 14 failures, the 22 old cases OK), `tests.test_records_cut` 10 OK at head; the review's repros of F1 to F5, L3, L4, L7 under `--go` on scratch fixtures: each exit 2, one refusal, both repos' listing and status unchanged; hygiene `--require-private` tree and `--commits main..HEAD` exit 0; `make check` queued on this head |
| P2 the phase 2, if rr7-way-in is on main | not done: main's last eight show no rr7-way-in merge (head f1135d5, hn1-help-next's); a later act |

## Next act

The gate's line; then the phase 2 once rr7-way-in is on main: `git merge main`, n263 to n268 renumbered after main's highest, the plugin version if the rules ask, the README source under 16,384 B.

## Handover

- decide, owner: coordinator. The six NICE rows pass `NICE_TO_HAVE.md`'s 24,576 B bound, so seven of its oldest S4 rows moved to `history/NICE-overflow.md` (outside build 1's may touch), as ak12-polish did; the packet's may touch now names it. Consumer: the landing.

- choice: F3 refuses the flags (`git ls-files -v`: lowercase or `S`) on records; it does not compare bytes. Consumer: review.
- choice: F4 compares the working `.hygiene-allow`'s bytes with HEAD's, so an edit hidden by a flag on it is refused too; an absent one the clone ignores is refused, since the cut's `git add` would fail. Consumer: review.
- choice: F5's upstream is left out of L3's tips, so an upstream past HEAD is one line (behind), not two. Consumer: review.
- choice: L4 compares every fetch and push URL; a local path or `file://` URL by its real path, any other case-folded, less a trailing `/` or `.git`. Consumer: review.
- choice: the stray-file refusal case now excludes its one file rather than `repos/`, since `repos/` ignored is F2's refusal. Consumer: review.
- choice: build 1's acceptance 9 (the dry run against a real sibling checkout) was not rerun: this round's brief allows the script on scratch fixtures alone. Consumer: coordinator.

## Exit

