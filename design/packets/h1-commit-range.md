# Packet H1: `scripts/hygiene --commits <range>`, and `land` runs it

| item | value |
|---|---|
| from | the finding of 2026-11-09 (`FINDING-2026-11-09-history-hygiene-probes/`): the scan reads the tree only, so a term added then removed on a branch enters public history at the merge |
| pin | agentik-commons main d76aef1, pushed; worktree `.claude/worktrees/h1-commit-range`, branch `h1-commit-range`. Part B (§6) pins agentik-hq f749553 |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no `relay`/`agentik relay` `run`, `plan`, `gate`, `stop`, `kill`, `clean`, `resume`, no relay binary by hand, nothing under `~/.local/state/agent-relay`; tests use an invented list via `$AGENTIK_HYGIENE_PRIVATE`; never read the private list, never print, write or commit a matched line or a private term |
| may touch | `scripts/hygiene`; `tests/test_hygiene_commits.py`; `GUIDE.md` (§6 only); `NICE_TO_HAVE.md`; this packet as `design/packets/h1-commit-range.md`; `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash; read the job's code from its line |
| acceptance | `python3 -m unittest tests.test_hygiene_commits tests.test_hygiene`, PATH's `python3` the 3.9 then a 3.12 (the shebang runs it): C1 to C12 green (d76aef1: `12 failed`); `tests/test_hygiene.py` unedited; `scripts/hygiene` exit 0; verify green |
| budget | a commit per group by explicit path, the packet first; `scripts/hygiene` green before every commit; stop at 90 tool calls or 140k context, with a resume line. `claude-opus-5-5` |

## 1. What the source says

- **Tree only.** `scripts/hygiene:249-258` at d76aef1: `files()` is `git ls-files -co`; `parse_args` (`:145-164`) exits 2 on `--commits`.
- **History keeps what the tree lost.** `histscan.py` on agentik-session `origin/main`: private groups, 22 added and 2 message lines in 13 of 449 commits; the tree scan exits 0. The prototype, rules applied: session 25 commits with a hit, decisions 5 of 112, commons 0 of 119. All pushed: out of scope.
- **Messages.** Commons' last 118 commits: `email` 118 message lines (`Co-Authored-By:`), `sibling` 16.
- **One copy.** `shasum ~/code/agentik-*/scripts/hygiene`: 8 of 8 `b478c79`. Seven tool repos pin it in `scripts/vendored.sha256`, checked by their `make check`; hq `scripts/suite` reports `vendored` drift; commons `scripts/sync <repo>` writes copy and pin.

## 2. Rulings

- R1. `--commits RANGE` scans the range instead of the tree, with `--json`, `--allow`, `--repo`, `--require-private` as today; an empty RANGE or one opening `-` is usage, 2. Git gets `--end-of-options RANGE --`.
- R2. `git log -p`, flags no config moves: `-c core.quotePath=false -c log.showSignature=false --no-color --no-ext-diff --no-textconv --no-renames --diff-merges=off --full-index --src-prefix=a/ --dst-prefix=b/ --format=%x00%x01%H%n%B%x00%x02`. Read by `readline(CHUNK)`; a longer line comes in pieces, each led by the last `OVERLAP` bytes, counted once. Git's non-zero exit, read after the stream, is exit 2: a cut stream is never clean.
- R3, lines. A hunk's `+` line, on its `diff --git` path (split at the middle, equal sides under `--no-renames`; C-quoting undone); a `new file mode` path is a line; removed and context lines never. `sibling` skips `history/sittings/`. `renamed` is not scanned and leaves `groups`: its rule is for live files, and history keeps old names by design.
- R4, binaries. On `Binary files ... differ` with a non-zero new blob, `git cat-file blob <oid>` through the tree's streamer (`stream` refactored to `stream_fh(fh)`): `home`, `secret`, `email` over printable runs, UTF-16 as text.
- R5, the allowlist is the head's: the working tree's `.hygiene-allow` (or `--allow`), loaded once. One reviewed policy, the tip's; a row added and dropped inside the range blesses nothing (C3); each commit's own tree would let the commit adding a term bless it, at a git read per commit.
- R6, messages. Each line of `%B` under every group but `sibling` and `renamed` (public tool names, which messages name routinely); no allowlist; the row's path is `(commit message)`. `email` skips a `Co-Authored-By:` or `Signed-off-by:` line, an identity git publishes in the header anyway.
- R7, merges. `--diff-merges=off`: a merge's message is scanned, its diff never; what it brings is in the range (C10) or behind it.
- R8, output. The tree's shape plus `commits: {"scanned": n, "hit": [12-hex shas]}`; `oversize` counts lines read in pieces. Text adds `commits: N scanned, K with a hit outside the allowlist: <shas>`. Never a line. Exits as today.
- R9, docs. The docstring and `USAGE` name `[--commits RANGE]` (Part B reads `--help`). GUIDE §6, after "exit 1 on a hit, 2 on usage.": "`--commits <range>` scans a range's added lines and messages instead, under the head's allowlist; before a push, `scripts/hygiene && scripts/hygiene --commits origin/main..main`."

Tests in `tests/test_hygiene_commits.py`, the probe's copy; at d76aef1 C1 to C11 exit 2 `unknown argument: --commits`, C12's help lacks the flag.

| C | test |
|---|---|
| 1 | added then removed: a hit, the tree scan 0, `hit` the adding commit |
| 2 | a message hit; `sibling` and a trailer's `email` none |
| 3 | the head's allow row rules; one added then dropped blesses nothing |
| 4 | a term only in a removed line: none |
| 5 | a term in a file deleted later: a hit |
| 6 | no matched text on stdout or stderr, text and `--json` |
| 7 | a bad range: 2, stdout empty; no, empty or `-` value: 2 |
| 8 | an empty range: 0, `scanned` 0 |
| 9 | sittings skip `sibling`; no `renamed`; a binary's `home` and no private hit; a new path is a line |
| 10 | a merge's message is scanned, its side's diff counted once |
| 11 | a 3 MiB line, a path with a space and an accent, four hostile `git config` keys |
| 12 | `--help` names `--commits RANGE` |

On the prototype (`partA-hygiene.patch`) C1 to C12 and `test_hygiene.py` are green under 3.9.6 and 3.12.13, its tree scan clean. Bound: 500 commits, a 62 MB diff, an 8 MB line: 5.6 s, the scan's max RSS 23 MB (git log's 154 MB).

## 3. Interfaces

New: `--commits`, `scan_commits`, `stream_fh`, `log_pieces`, `header_path`, `unquote`, `MESSAGE`, `MESSAGE_SKIP`, `TRAILER`, `SHORT`, `LOG`; `--json`'s `commits` there. The tree scan stands.

## 4. Findings that name this row; the landing

Commons keeps no ledger. Bearing: agentik-hq 6 (3.9, stdlib), 5 (push after a clean scan: both, once R9 stands), 17 (Part B is small); the house ledger's 25, exit codes report the task (git failing stays 2).
Order: (1) Part A lands in commons, pushed. (2) Part B in hq, independent of (1). (3) A row per repo from commons' main: `scripts/sync ~/code/agentik-<repo>`, commit `scripts/hygiene scripts/vendored.sha256` alone (any other path: stop, drift), land, push: session, decisions, agents, relay, observer, respeak, dev-github.
The orchestrator's lines after (2), hq `CLAUDE.md`: step 9 "Hygiene green" reads "Hygiene green (`scripts/hygiene && scripts/hygiene --commits origin/main..main`)"; step 7's "`scripts/hygiene` when present" adds "and `--commits main..<sha>`". The push's range covers the merge's own message, which the landing cannot.
No pushed history is rewritten. NICE: an evil merge's lines; author headers.

## 5. Forbidden reads and report

The private list, transcripts, `~/.local/state`. Six lines: head sha, gate id and code, C1 to C12, choices, leftovers.

## 6. Part B, agentik-hq: `scripts/land` runs the range

| item | value |
|---|---|
| pin | agentik-hq main f749553 (`scripts/land` a54f3f4); worktree `.claude/worktrees/h1b-land-range` |
| may touch | `scripts/land`; `tests/test_land_range.py`; `tests/test_land.py` (B4's line); `history/sittings/*-hq.md` |
| acceptance | `/usr/bin/python3 -m unittest discover -s tests -p 'test_land*.py'`: R1 to R5 green (f749553: `5 failed`); the verify row on this worktree green |

- B1. After the tree scan, `takes_commits`: `scripts/hygiene --help` exits 0 and names `--commits`. Then `--commits refs/heads/main..<full sha>` in the worktree; non-zero is `red hygiene exit <code>` before the merge, main untouched.
- B2. An older copy is told by `--help`, not a usage exit (its `--commits` exits 2, as git failing does). The run goes on, notes `hygiene: scripts/hygiene has no --commits; refs/heads/main..<sha> not scanned`, and the ok line ends `, range not scanned`. A failing `--help` is older.
- B3. A repo without `scripts/hygiene` stands as today.
- B4. `test_a_the_steps_run_in_order_hygiene_in_the_worktree` expects `["check", "hygiene", "hygiene"]`, its fake showing the probe: the one existing test edited. On the prototype (`partB-land.patch`) the other 108 and R1 to R5 are green under 3.9.6 and 3.12.13.

Fork for the orchestrator: B2's suffix on the verdict line (proposed: `gate wait` reports that line), or the note alone.
