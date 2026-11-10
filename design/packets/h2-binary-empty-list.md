# Packet H2: a private term in a binary is a hit; `--require-private` wants a term

| item | value |
|---|---|
| from | agentik-hq NICE n11, n12 (S3; h1 Part B's F5, F6); probes in agentik-hq `history/sessions/PACKET-2026-11-10-hygiene-h2-probes/` |
| pin | agentik-commons main f0fba84; worktree `.claude/worktrees/h2-binary-empty-list`, branch `h2-binary-empty-list` |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no `relay`/`agentik relay` `run`, `plan`, `gate`, `stop`, `kill`, `clean`, `resume`, nothing under `~/.local/state/agent-relay`; tests use an invented list via `$AGENTIK_HYGIENE_PRIVATE`; never read the private list, never print, write or commit a private term |
| may touch | `scripts/hygiene`; `tests/test_hygiene.py`; `tests/test_hygiene_commits.py` (line 170 only); `NICE_TO_HAVE.md`; this packet as `design/packets/h2-binary-empty-list.md`; `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash; read the job's code from its line |
| acceptance | `python3 -m unittest tests.test_hygiene tests.test_hygiene_commits`, PATH's `python3` the 3.9.6 then a 3.12: 61 OK (f0fba84 with the tests alone: `failures=7, errors=1` under each); `scripts/hygiene` exit 0; verify green |
| budget | a commit per group by explicit path, the packet first; `scripts/hygiene` green before every commit; stop at 60 tool calls or 120k context, with a resume line. `claude-opus-5-5` |

## 1. What the source says (f0fba84)

- **Binary.** `read_lines` (`scripts/hygiene:412-429`): UTF-16 (`:354-368`) is text; else a NUL in the first 8 KB is binary, and `pieces` (`:371-375`) yields its printable runs of 8+ bytes, tagged `BINARY_GROUPS` (`:140`: home, secret, email). The loop (`:495`) skips every other group, so a private row under its own group never runs.
- **Range.** A `Binary files` line (`:673-674`) streams the new blob through `stream_fh` (`:386-409`); `matches` (`:593-595`) filters by the same tag. `p2-binary.sh`: three binaries in the tree, exit 0; added then removed, `--commits` exit 0.
- **List.** `load_private` (`:223-252`) raises under the flag only on a missing or unreadable file; no row returns `[]` and the generic groups scan. `p1-empty-list.sh`: comments, blanks or zero bytes under the flag, tree and range exit 0, the term in both.

## 2. Rulings

1. With `--require-private`, a list missing, unreadable, or holding no row once comments and blank lines are dropped exits 2 before any scan, stdout empty, one stderr line naming it. Without the flag nothing changes.
   The lines: `hygiene: no private list at P; nothing scanned (--require-private)`, likewise `the private list at P is unreadable; nothing scanned` and `the private list at P holds no term; nothing scanned`.
2. A binary's printable runs keep today's scan by the in-file patterns of `home`, `secret`, `email`. The private rows, whatever their group, scan its whole content decoded as UTF-8 with bad bytes replaced (the text path's decoder), so each regex and its case rule run unchanged: one line per file, per 1 MiB chunk when streamed.
3. A row is private by identity (not in `COMPILED`): a private `home` row moves from the runs to the whole content, never counted twice. Both scans: `pieces` adds `(buf.decode("utf-8", "replace"), PRIVATE_ONLY)` for a binary; one `wanted(names, name, rx)` replaces the filters at `:495` and `:594-595`.
4. A hit reads as today's: path, group, lines; never the term.
5. The docstring's binary and `--require-private` sentences and its exit-2 list. No new flag; the allowlist's rules and `--commits` stand; GUIDE untouched.
6. One row in commons `NICE_TO_HAVE.md`: a term under an encoding inside a binary (UTF-16, base64, deflate as in PNG zTXt, zip, PDF) is not found, nor a non-ASCII term a streamed chunk's cut splits.

Cost (`p3-cost.sh`, 50 MB binary, tree and range alike): 3 rows, random 1.9 to 3.0 s, printable 2.7 to 3.9 s; 30 rows 10.4 and 14.0 s. Max RSS random 28 to 215 MB (those bytes as a text file: 14.5 s, 221 MB at f0fba84), printable 33 to 40 MB. The suite tracks 10 binaries, the largest 389 KB.

## 3. Tests

`tests/test_hygiene.py`, class `PrivateListTest` (the probe's `tests.patch`):

| H | test | f0fba84 |
|---|---|---|
| 1 | comments, blanks, zero bytes under the flag: 2, one line naming the file, `nothing scanned`; tree and `--commits` | red |
| 2 | missing, a directory, not UTF-8: that line shape | red |
| 3 | no flag, an empty list: exit by the generic groups, stderr empty | guard |
| 4 | a term in a run, uppercase beside UTF-8 bytes, non-ASCII, 4 bytes: a hit each; lan, sibling none; no term printed | red |
| 5 | the term after 5 MiB of a binary: a hit, `oversize` 1 | red |
| 6 | a binary added then removed in a range: a hit, `hit` the adding commit | red |

Edited as ruling 2 makes them: `test_nul_file_scans_secret_and_email` and `test_binary_scanned_for_home_over_printable_runs` gain the binary's `person` row; C9 (`tests/test_hygiene_commits.py:170`) asserts `("blob.bin", "private")` 1.
`setUp`'s `blob.bin` (`:79`) takes the lan fixture, so it still guards a generic skip and five counting tests stand. On the prototype (`hygiene.patch`) the 61 are green under 3.9.6 and 3.12.13, commons' suite 171.

## 4. The landing

Commons keeps no ledger. Bearing: agentik-hq 6 (the 3.9 floor, stdlib), 5 (push after a clean scan). Syncing the vendored copies into the other repos is outside this packet: a later row per repo, as in h1's order (3). agentik-hq `scripts/land` passes ruling 1's line through unparsed (`:446-448`).

## 5. Forbidden reads and report

The private list, transcripts, `~/.local/state`. Six lines: head sha, gate id and code, H1 to H6, choices, leftovers.
