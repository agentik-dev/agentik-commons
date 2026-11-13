# Packet H2b: a private row led by `.*` reads a binary in linear time

| item | value |
|---|---|
| from | agentik-hq's brief h2 of 2026-11-12 (`history/sessions/BRIEF-2026-11-12-commons-h2-hygiene-binary.md`), R1 to R4; the tree's entry 37; this repo's NICE n13 |
| pin | agentik-commons main 9f20220; worktree `.claude/worktrees/h2-hygiene-binary`, branch `h2-hygiene-binary` |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no `relay`/`agentik relay` `run`, `plan`, `gate`, `stop`, `kill`, `clean`, `resume`, nothing under `~/.local/state/agent-relay`; no `claude` process; no ledger edited; tests use an invented list via `$AGENTIK_HYGIENE_PRIVATE`, never the private list |
| may touch | `scripts/hygiene`; `tests/test_hygiene.py`; `NICE_TO_HAVE.md` (n13 out, n17 in); this packet as `design/packets/h2-hygiene-binary.md`; `history/sittings/2026-11-12-1.md` |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id> --strict` in one background Bash |
| acceptance | 1 to 5 below, each measured at 9f20220 by a probe of made-up terms (scratch, not committed); `python3 -m unittest tests.test_hygiene tests.test_hygiene_commits` OK; `scripts/hygiene` exit 0; verify green |
| budget | a commit per act by explicit path, the packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. What the source says (9f20220)

- Packet h2-binary-empty-list landed before this brief was cut: R1 and R3 hold at the pin. A binary's printable runs scan the private rows, and a row no run hit scans the binary's whole content decoded as UTF-8 (`pieces`, `line_hits`); `load_private` exits 2 on a list holding no row under `--require-private`.
- The whole content is one line per file (per 1 MiB chunk when streamed). `.` matches a NUL, so a binary with no newline is one line, and a row led by `.*` backtracks over the rest of it from every start: quadratic (NICE n13).

## 2. Rulings

1. R1 stands as built: a private term in a binary is a hit in the tree and in `--commits`, the file and the row named, never the bytes. An encoded term (UTF-16, base64, deflate) stays NICE n12.
2. R2: a binary's whole content is scanned with each control byte but the tab (NUL and newline among them) and each byte UTF-8 cannot decode read as a newline, so a private row's `.` and its `^`/`$` (multiline) stop there. A row's cost is then bounded by its longest span of text, as a text file's is by its longest line. The count stays one line per file (per chunk). Chosen over a span cap: a byte table and a `replace`, no window to tune. NUL alone was measured first and missed the bound: random bytes with no newline, 20 MB, 26.7 s (a NUL only every 256 bytes); the wider set 1.3 s. A term holds no control or bad byte, so no term is lost; the residual, a long newline-free span of text, binary or not, is NICE n17.
3. R3 stands as built: `--require-private` with a list of only comments and blank lines exits 2, one stderr line `the private list at P holds no term; nothing scanned (--require-private)`.
4. R4: a text file's lines, the allowlist, the built-in groups, every message and exit are unchanged; the docstring's binary sentence names the NUL rule.

## 3. Acceptance (probe of made-up terms, `person<TAB>term` and `person<TAB>.*term`)

| # | line | 9f20220 |
|---|---|---|
| 1 | a term in a binary (NUL in its head), tree; the same added then removed, `--commits` | red, exit 1, `pic.png person 1` in both (already met) |
| 2 | the same term in a text file, tree, range, `--json` | exit 1, `t.txt person 1`; the output is the baseline |
| 3 | 20 MB binary, no newline, a `.*term` row, tree and range: NUL-padded and random bytes | killed at 60 s, each of the four |
| 4 | `--require-private`, a list of comments and blanks: exit 2, one line; one row: exit 0; no flag: exit 0 | as wanted (already met) |
| 5 | the script's tests; `make check` through the queue | green |

## 4. Tests

`tests/test_hygiene.py`, class `PrivateListTest`, `test_h9`: a 256 KiB binary of NUL padding and control bytes, no newline, a 4-byte term between NULs, a `.*` row: one hit in the tree and in the range, each run under a 30 s timeout. At 9f20220 the run is quadratic on 256 KiB (the refuter measured 75.7 s on 64 KiB) and times out.

## 5. The landing

Commons keeps no ledger. Syncing the vendored copies is the coordinator's round after this lands. NICE n13 leaves; n12 stays; n17 files R2's residual.

## 6. Forbidden reads and report

The private list, transcripts, `~/.local/state`. The report: head sha, gate id and line, acceptance 1 to 5 at the pin and now, R2's time on 20 MB.
