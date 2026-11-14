# Packet rp1-shapes: the scanner knows more token shapes, and the suite's `lib/` holds its byte copy

| item | value |
|---|---|
| from | agentik-hq's brief rp1 of 2026-11-13, R1 to R6; hq design/22 §3 item 4(c) and §9 (R1-F6); level S2; the first row of the suite's issue reporter |
| pin | agentik-commons main b62ddad (suite 0.6.1); worktree `.claude/worktrees/rp1-shapes`, branch `rp1-shapes`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; every token in a test random and assembled at run time; made-up names |
| may touch | `scripts/hygiene`; `plugins/suite/lib/agentik_hygiene.py`; `tests/test_rp1_shapes.py`; `tests/test_agentik_suite.py` (the `STDLIB` line alone); this packet; `history/sittings/2026-11-13-14.md` |
| verify | `make check`, once, last, through the gate queue, `--strict` |
| acceptance | 1 to 7 below; `python3 -m unittest tests.test_rp1_shapes` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"We should also have a way of reporting issues with agentik tooling that submits issues to github with relevant info to diagnose on this computer but with warnings and ways to remove identifying or private information." The reporter scrubs what it gathers with this scanner's own tables, so a token shape the scanner lacks is one an issue could carry. This row builds first and alone; four rows wait on its landing.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names in fixtures and the packet).

- R1, the shapes. The `secret` group of `scripts/hygiene` gains, each as one more pattern of its tuple: GitHub's four other token prefixes (OAuth, user-to-server, server-to-server, refresh, beside the classic one it has); a JWT (three base64url parts joined by dots, the first two opening with the letters a JSON object's base64 opens with); the prefixes of six vendors' tokens: Slack's five, OpenAI's key with and without its project part, Google's API key, npm's, GitLab's personal token and Hugging Face's. Each wants a body long enough that a word of prose is no hit (20 characters or more unless the vendor's token is shorter). `secret` stays case-sensitive.
- R2, the file does not match itself: each pattern brackets a letter as the file's others do, so the scan of its own tree stays where it was. No new group, no change to another group, no new flag.
- R3, nothing else joins. A URL's userinfo, a `password=` assignment, a bearer or basic header and a key block's body stay in the reporter, since in a tree's scan they would hit code; one sentence of the docstring says so where it names the groups.
- R4, the copy. `plugins/suite/lib/agentik_hygiene.py` is a byte copy of `scripts/hygiene`, placed by `cp`, mode 0644. It is imported, never run; nothing in the package imports it yet.
- R5, the pin and the import list. `tests/test_rp1_shapes.py`: the copy is byte-equal to `scripts/hygiene`; as a module it gives `COMPILED`, `private_path` and `load_private`. In `tests/test_agentik_suite.py` one line changes: `STDLIB` gains `"agentik_hygiene"`, `"hashlib"` and `"unicodedata"`, which the four rows after this one import.
- R6, not this row's: the package (`plugins/suite/lib/agentik_suite/`), `.hygiene-allow`, `README.md`, `plugin.json`, `GUIDE.md`, `NICE_TO_HAVE.md`, the `Makefile`, `tests/test_hygiene.py` and any other test file.

## 3. Acceptance

Measured at b62ddad, scanner SHA-256 `460759c85938`, with `tests/test_rp1_shapes.py` run against it: each of the 16 shapes (GitHub's four, a JWT, Slack's five, OpenAI's two, Google, npm, GitLab, Hugging Face), one random line each, counts 0 under `secret`; the twelve prose lines count 0; the copy does not exist (lines 4 and 5 fail); `STDLIB` holds 16 names; `scripts/hygiene --json` in the worktree: every group's `outside_lines` is 0.

| # | line |
|---|---|
| 1 | for each shape of R1, a line assembled at run time from parts: `scripts/hygiene --json --repo <a temp repo holding it>` counts 1 line under `secret`; the same line with its body cut to 8 characters counts 0 |
| 2 | twelve lines of prose and code that hold a prefix's letters inside a longer word or with a short body (a slug, a test's name, a version): `secret` counts 0 |
| 3 | `scripts/hygiene --json` in the worktree: every group's `outside_lines` equals what it prints at the pin (0 each) |
| 4 | `cmp scripts/hygiene plugins/suite/lib/agentik_hygiene.py` prints nothing; the test of R5 holds it |
| 5 | `/usr/bin/python3 -c 'import sys; sys.path.insert(0, "plugins/suite/lib"); import agentik_hygiene as h; print(len(h.COMPILED))'` prints `6` and writes nothing to stderr |
| 6 | `python3 -m unittest tests.test_agentik_suite` passes with the three names in `STDLIB` and no other line of that file changed (`git diff --stat` shows 1 insertion, 1 deletion there) |
| 7 | `make check`, once through the gate queue, green |

## 4. Not built

The reporter's own shapes and its scrub (rp2). The other checkouts' copies of the scanner: `scripts/sync` carries them after the landing, the coordinator's act. A token broken across two lines.

## 5. The landing

`plugin.json` stays as it is: a later row of the reporter takes the version. After the merge, `scripts/sync` brings the new `secret` patterns to every repo; a repo whose tree holds one of the new shapes goes red at its next scan.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, a relay ledger. The report: head sha, the gate's id and exit, acceptance 1 to 7 at the pin and now.
