# Packet rr3-records-guard: the scanner's `records` group

| item | value |
|---|---|
| from | agentik-hq's brief rr3-records-guard of 2026-11-18, G1 to G6, and its fix of review 1, C1 to C5; hq design/28 §3 items 5, 7, 8, 10 and 11 as amended, and §11's leads 3 and 4; level S3 |
| pin | agentik-commons main 8ff5214 (rr2 landed); the fix at the branch's 1e54c91; worktree `.claude/worktrees/rr3-records-guard`, branch `rr3-records-guard`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no tool synced; no test reads the live private list, the live home, the live state or a real repo's git config; made-up names in fixtures |
| may touch | `scripts/hygiene`, `plugins/suite/lib/agentik_hygiene.py` (its byte copy, held by `tests/test_rp1_shapes.py`), `tests/test_hygiene_records.py` (new), `scripts/agentik_records.py`, `plugins/suite/lib/agentik_records.py`, `plugins/suite/.claude-plugin/plugin.json`, `tests/test_hygiene.py`, `tests/test_hygiene_commits.py`, `GUIDE.md` (§12), `NICE_TO_HAVE.md`, `history/NICE-overflow.md`, `design/packets/rr3-records-guard.md`, `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | the new and touched test files directly; `make check` once, last, through the gate queue; `scripts/hygiene --require-private` on the tree and on `--commits main..HEAD` |
| acceptance | 1 to 3 below |

## 1. The finding

hq design/28 §3 item 5 names one declaration, the line `records: out` in the tracked `.hygiene-allow`, and item 10 a judged scanner group that holds a declaring repo's record names out of its tree and its pushes. At the pin no group `records` exists, and `parse_allow` reads `records: out` as an allow row of an unknown group `out`: a bad entry (exit 2) under `--require-private`, so a declared repo cannot pass its own scan.

## 2. Rulings

- G1, the declaration: a line declares by the resolver's rule exactly (`scripts/agentik_records.py` `_declares`: a row of `splitlines()` equal to `records: out` after `rstrip()`), and it is no allow row. Any other line naming the group `out` is a bad entry, so the two readers never disagree in silence: rr2 review 1's near misses (`records: out # reason`, `records:  out`, an indented line, `records: "out"`, a BOM before the line) declare nothing in either and exit 2 in the scanner.
- G2, the group `records`, judged: in a tree that declares, a path under a record name is a hit. The names, at the repo's root: `history/`, `design/packets/`, `HANDOFF.md`, `NICE_TO_HAVE.md`, `OPEN-QUESTIONS.md`, `bugs/`, `relay/queue.yaml`, `.hygiene-live`. The relay gives its plan no copy by another name (agentik-relay b735980 tracks `relay/queue.yaml` alone and writes none), so `relay/queue.yaml` stands alone. An allow row naming `records` is a bad entry, as a `secret` row outside `tests/fixtures/` is. Counts only: one line a path.
- G3, the tree scan: the scanner's own file set (tracked and untracked-not-ignored). The tree declares when the working `.hygiene-allow`, the one at `HEAD` or the `--allow` file declares, so an uncommitted removal of the line does not switch the guard off.
- G4, the range scan: each path a commit of the range adds or modifies under a record name is a hit where the tip declares or the base declares; a removal is none. A range whose base declares and whose tip does not is one more hit, on the path `.hygiene-allow`. Each end's declaration is read from its blob, as `load_allow_tip` reads the tip's allow file; the base is the range's negative revisions (any declaring), none for a range without one.
- G5, the GUIDE says where the guard runs: each `make check`, the landing's and the publish's scans, and a pre-push hook where the repo has one. Lead 4 (a repo extends the names from its own allow file) is a row in `NICE_TO_HAVE.md`.
- G6, the words: the scanner's docstring, GUIDE §12's guard paragraph. No tool is synced here.
- C1 (review 1's F2), a merge's records: in the range scan a merge's paths added or modified against its first parent are judged for `records` as any commit's; the other groups keep `--diff-merges=off`.
- C2 (F1, F3), the declaration's read never fails a scan: read for the declaration alone, an entry that is no regular file declares nothing and bytes that are not UTF-8 decode with `surrogateescape`; the read as rows fails as at the pin.
- C3 (F5), a path's root name is compared with the record names case-folded, in both scans.
- C4 (F4), the resolver runs git with `--no-replace-objects`, as the scanner does; the suite's copy follows, suite 0.7.36.
- C5, each of F1 to F5's probes a test, red at 1e54c91; the tests run under `/usr/bin/python3` 3.9 too.

## 3. Interfaces

- The group shows in `groups` (and the text table, after the private list's groups) only where the scan declares: the tree, or either end of the range; an undeclared scan prints what it printed at the pin. A hit is in `files` as `{"path", "group": "records", "lines": 1}` (per commit in a range, so a path two commits touch counts 2).
- The base-declares-tip-does-not hit is `.hygiene-allow` with group `records`, one line, its sha the tip's.
- The names match case-folded (C3).

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `python3 -m unittest tests.test_hygiene_records`: a declared tree with a record tracked, untracked, and with the line removed only in the working file (exit 1); a declared tree with none (exit 0); an undeclared tree with records (no hit); a `records` row and an `out` line other than the declaration (exit 2); a range adding a record under a declaring tip; a range whose base declares and whose tip does not; probe5's lines through both readers, the same answer | red: no group `records`, the declaration a bad entry |
| 2 | `scripts/hygiene --require-private` on the tree and with `--commits main..HEAD`: exit 0, the other groups' counts as at the pin | exit 0; home 23 9, lan 2 1, sibling 243 67, renamed 2 2, person 1 1, the rest 0 |
| 3 | `make check` through the gate queue, green on the head handed back | green at 8ff5214 (rr2's landing) |
| 4 | C5: `-k FixTest`, under `python3` and `/usr/bin/python3` | at 1e54c91: 9 of 11 red |
