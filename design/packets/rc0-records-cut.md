# Packet rc0-records-cut: `scripts/records-cut` moves a repo's records to its holder and declares them out

| item | value |
|---|---|
| from | the coordinating repo's brief rc0-records-cut of 2026-11-20, R1 to R7, on the row's design D1 to D4 (entry 63, design/28 §3 items 2, 3, 5, 7, 10 and 20); level S3 |
| pin | agentik-commons main b4b4cc8; build 4's phase 2 merged main 65e15b8, which holds hn1-help-next and rr7-way-in; worktree `.claude/worktrees/rc0-records-cut`, branch `rc0-records-cut`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; `--go` only inside a test's temp folders; no vendored script edited; made-up names in fixtures |
| may touch | `scripts/records-cut`, `tests/test_records_cut.py`, `GUIDE.md` (new sentences in §12), `NICE_TO_HAVE.md` (rows), `history/NICE-overflow.md` (its oldest S4 rows, for the bound), `.hygiene-allow` (the coordinator's allow row for this test's made-up remote URLs), `design/packets/rc0-records-cut.md`, `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | `python3 -m unittest tests.test_records_cut` directly; `make check` once, last, through the gate queue; `scripts/hygiene --require-private` on the tree and on `--commits main..HEAD` |
| acceptance | 1 to 11 below |

## 1. The owner's words

Entry 63 of the coordinating repo's ledger: "Each of agentik's public tools keeps its working records in agentik-hq. As a tool's row lands, its charters, packets, wish list and questions move to agentik-hq/repos/<tool>/ and leave the public tree in one commit; what is already pushed stays in the public history (design/28)." Entry 37: "Never commit. The tool repos are public. Commit no hostname, address, email, person's name, account detail, or private repo's name or path; examples use made-up names." Nothing in the script or its words names a tree, an hq or an org: the holder is an argument.

## 2. Rulings

- R1, the verb: `scripts/records-cut --repo <clone> --holder <repo> [--go]`, stdlib Python under the repo's `python3`, git's environment cleared as the resolver clears it. Without `--go` it writes nothing anywhere and prints the record paths at `HEAD` (counts by name, files, bytes), the destination, every refusal that applies, and the plan. Exit 0 a clean dry run or a finished move, 2 a refusal, 1 a failed step.
- R2, the names: the scanner's `records` group, root only, case-folded; held once in the script, a test holds them equal to `scripts/hygiene`'s.
- R3, the destination: `<holder's top>/repos/<the clone's main checkout's folder name>/`, each record at its relative path.
- R4, the refusals, each one line naming what and where: not a main checkout (a worktree, bare, no repo); a dirty tree; `HEAD` ahead of its upstream or with none; a local branch or worktree whose commits past `HEAD` add or change a record (at most ten listed); a record path that is a symlink or holds one; a destination that exists and is not empty; a holder that is no repo, is the clone or shares its git folder, is dirty under the destination, or declares `records: out`; `agentik.records` already set; `.hygiene-allow` already declaring or holding a `records` row; no record found.
- R4a, review 1's round (each refused before anything is written, in the dry run and under `--go`, one line naming the path or ref): F1, a symlink at `<holder>/repos` or `repos/<name>`, or a destination whose real path is outside the holder's tree or inside the clone; F2, a destination path the holder's ignore rules match (`git check-ignore --no-index`); F3, a record the index flags assume-unchanged or skip-worktree (the flags are refused, the bytes not compared); F4, a `.hygiene-allow` in the tree that is absent at HEAD or differs from HEAD's, or an absent one the clone ignores, never overwritten; F5 and L3, a HEAD behind its upstream, and a remote-tracking branch other than the upstream with a record commit past HEAD; L4, a holder with a fetch or push URL equal to one of the clone's (a local path by its real path); L7, a submodule at, under or holding a record name, as a symlink is. L5 is ruled: the repo's commit hooks stay on. L1, L2, L5, L6, L8 and L9 are NICE n269 to n274.
- R4b, review 2's round: F1 to F4 are one proof. Under `--go`, after the copy and its sums and before the clone changes, the holder's own git must take every copy by the printed `git add -- repos/<name>`: each copy's folder's `rev-parse --show-toplevel` is the holder's top, and `git add --dry-run -- repos/<name>` exits 0 and names each copy, so an ignore rule (one copied among the records too), a sparse rule or a submodule drops none. Where it would not, the script removes exactly the files and folders it made, changes nothing in the clone, and refuses (exit 2) in one line naming the first copy and why. Before the copy, in the dry run too: the destination's nearest existing folder in another repo's tree, a submodule the holder tracks at `repos`, the destination or under it, and a sparse checkout whose rules (`git sparse-checkout check-rules`) leave a destination path out; the plan says the proof runs under `--go`. F5: remotes are compared as (host, path), the scheme, a user, a port, the short `host:path` form, a trailing `/` and `.git` dropped and both case-folded; a local one by its real path. L3: `.hygiene-allow` is HEAD's where `git diff --quiet HEAD` finds no change and `git hash-object --path` is HEAD's blob. Review 2's L1, L2 and L4 are NICE n275 to n277.
- R5, `--go`, stopping at the first failed step with one line of what was done and what to undo: copy each blob at `HEAD` with its mode and compare sha256s; `git rm` the records, add `records: out` to `.hygiene-allow`, stage by explicit paths, one commit with a one-line message naming no holder; set the key; then the proofs (resolver `out` with that folder; the clone's `scripts/hygiene` green in tree mode and over `HEAD^..HEAD`; `HEAD^`'s tree less the records equals `HEAD`'s less the new line). A failed proof exits 1 and reverts nothing. Last, the holder's commit line and the push order: the clone first.
- R6, never: a commit in the holder, a push, a history rewrite, a remote, a tag, a worktree, another branch, a git identity, or a file that is not a record at `HEAD`.
- R7, the words: `GUIDE.md` §12 gains the cut; the script's header says the same; a `NICE_TO_HAVE.md` row where one is seen.

## 3. Interfaces

- `scripts/records-cut --repo <clone> --holder <repo> [--go]`; `-h` prints the usage; an unknown word or a missing value is usage, exit 2.
- stdout: the report (`repo`, `holder`, `destination`, `records at HEAD`, one line a name, one line a path, `plan`), then on `--go` one line a step done; stderr: `records-cut: refused: <what>: <where>` per refusal, `records-cut: failed: ...` for a failed step or proof.
- `RECORD_DIRS`, `RECORD_FILES`: the names, as the scanner spells them.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `-k test_dry_run_lists_and_writes_nothing`: every record name listed, a listing and `git status` of clone and holder unchanged, exit 0 | no script |
| 2 | `-k test_go_moves_commits_and_sets_the_key`: byte-equal, modes kept, untracked in the holder; one commit of exactly the records and the line; key set; resolver `out`; a second run refuses | no script |
| 3 | `-k test_each_refusal_alone` and `-k test_three_refusals_at_once`: exit 2, every one printed, nothing written | no script |
| 4 | `-k test_a_failed_step`: a read-only destination after the first copy, a refusing commit hook: exit 1, the line says what was done, no commit or key left | no script |
| 5 | `-k test_the_names_are_the_scanners` | no script |
| 6 | `-k test_the_clones_scanner_after_the_move`: green in tree mode and over `HEAD^..HEAD`, red with one record restored | no script |
| 7 | `-k test_the_folder_name_not_the_remotes`: the destination takes the folder's name; resolver `out` | no script |
| 8 | `scripts/hygiene --require-private --commits main..HEAD` exit 0; `make check` through the gate queue | green at b4b4cc8 (sy4's gate) |
| 9 | not a test: the dry run against one sibling tool checkout, read only | no script |
| 10 | R4a: `-k test_each_refusal_alone` gains 14 cases (F1 2, F2 2, F3 2, F4 3, F5 and L3 2, L4 2, L7 1), each refused alone in the dry run and `--go`, nothing written; the review's probes now refuse on scratch fixtures | each case red at 6cf05fa |
| 11 | R4b: `HolderTakesTest` (review 2's F1 to F4 fixtures: two ignore files among the records, a nested repo at `repos`, a submodule at the destination, a sparse cone without `repos`; `--go` exit 2, the clone and the holder as they were; the dry run refuses all but the ignore files; the proof alone refuses with the checks before the copy silenced), `RemoteSpellingTest`, `LineEndTest` | each red at fbf61b4 |
