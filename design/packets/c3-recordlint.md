# Packet c3: recordlint, the rule for records as tables

| item | value |
|---|---|
| from | agentik-hq HANDOFF 18 (build 7, the owner's word of 2026-11-01); `~/code/agentik-hq/design/05-records-as-tables.md` §2, §3, §4, §7 item 2, §12; d26's refuter F1 and F3 (below); hq entry 6 (commons is the home of the shared scripts) |
| pin | commons main c3e2223 (the `decisions` 0.11.0 line); worktree `~/code/agentik-commons/.claude/worktrees/c3-recordlint`, branch `c3-recordlint`, cut there |
| wall | this repo; read `~/code/agentik-hq` and the other `~/code/agentik-*` repos at main, never write there (a `git clone` from them into a scratch dir is a read); no push, `--amend`, rebase, merge, real `make install`, real `install-cli`; `claude` only as `claude plugin validate` and `claude plugin test plugin`; a test never writes under the live `~/.local`, `~/.claude`, `~/.config`; never touch `~/.config/agentik/hooks-follow-launcher`; no relay verb or binary; no `kill`, `pkill` or signal from a script; never a gate verb under a temp HOME; zsh here, `bash -c` for bash syntax; `rm -r` only as `"${VAR:?}"` |
| may touch | `scripts/recordlint` (new), `scripts/sync`, `Makefile`, `tests/` (new `test_recordlint.py`, fixtures under `tests/`), `tests/test_sync.py`, `GUIDE.md` §9, `NICE_TO_HAVE.md`, `history/NICE-2026-11-01.md` (by `git mv` only), `.hygiene-allow`, `README.md` only where it lists the scripts, this packet as `design/packets/c3-recordlint.md`, a charter under `history/sittings/` |
| acceptance | §2's acts; the fixtures; `sync` into a temp repo places `scripts/recordlint` and lists it in `vendored.sha256`; `make check` green, recordlint's line in it |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c "make check > <scratch log> 2>&1"`, then `agentik session gate wait <id>` in one background Bash, last. It exits 0 whatever the job's code: read the code from its line |
| budget | One commit per act. **Stop at 120k context or 90 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

Read first, by sections (`record <file> --sections`, then `--section`): design/05 §2, §3, §4, §12; this repo's GUIDE §4 (the test standard), §6 (hygiene), §9; `scripts/sync` whole; `scripts/hygiene:1-40,100-115`; `~/code/agentik-decisions/plugin/lib/decisions/backlog.py:20-60,190-230` (the reader recordlint must agree with). doclint (`~/code/agentik-decisions/scripts/doclint` or the agents copy) is the model for output and exit codes.

## 1. What this is

A stdlib checker at the 3.9 floor that holds `HANDOFF.md` and `NICE_TO_HAVE.md` to design/05 §2's tables, so the later packets can convert each repo and stay green. **Not here:** any other repo's conversion or resync (a-s19, h1, s52, d27, relay, r17); hq's pinned copy (h1); `backlog` (d26, landed).

## 2. Acts

0. This packet, committed first, as `design/packets/c3-recordlint.md`.
1. **`scripts/recordlint`.** `recordlint [FILE...]`, by default `HANDOFF.md` and `NICE_TO_HAVE.md` in the cwd; a missing file is skipped. Output `path:line: rule: detail`, exit 2 on any finding, 0 otherwise, as doclint. design/05 §4's rules 1 to 6, as written, with these two from d26's refuter:
   - **F1.** Inside a table, any line that is not a row (an indented line, a bullet, prose) is `non-row` at its line: `backlog.py:197` ends the table there silently, so the rows after it vanish from `backlog`.
   - **F3.** HANDOFF's header is exactly `| # | item | level | repo | where | state |`; each `repo` cell is a bare short name, `^[a-z][a-z0-9-]*$` and not `agentik-...` (`hq`, `suite`, `session`, ...), no backticks: `--order` matches it exactly.
   Cells split on unescaped pipes; `\|` in a code span is one cell. The NICE overflow file (`history/NICE-overflow.md`) is the remedy recordlint's rule-6 message names; recordlint writes nothing.
2. **Tests.** `tests/test_recordlint.py` with a fixture each for: skip (no canonical header), non-row (prose under a `##`; F1's indented line inside a table), a row over 400 characters, a duplicate `#` and `id`, a bad level, a bad state word, a wrong cell count, `\|` in a code span (green), a HANDOFF over 8,192 B, a NICE over 24,576 B, F3's header and `repo` cell, and a fully green HANDOFF and NICE. GUIDE §4's standard.
3. **`sync`.** Places `scripts/recordlint` (755) beside hygiene and lists it in `vendored.sha256`; `tests/test_sync.py` asserts both on a temp repo.
4. **commons runs it.** `make check` runs `scripts/recordlint` on this repo.
5. **GUIDE §9's rows paragraph.** design/05 §2's two shapes and its Cells paragraph, in GUIDE's voice, short; it names recordlint.
6. **commons' NICE.** design/05 §3: `git mv NICE_TO_HAVE.md history/NICE-2026-11-01.md`, and in that commit `history/NICE-2026-11-01.md: sibling` under the `NICE_TO_HAVE.md: sibling` row of `.hygiene-allow`. A new `NICE_TO_HAVE.md`: a title, one head paragraph naming the archive, then the table under a `##`, holding the S1 to S3 items you confirm open on main (design/05 counts 2 for commons); ids from `n1`. S4 and unlevelled items stay archived. recordlint green on it.
7. The gate, last.

## 3. The stop

Stop and report, committing what is there, on: a rule of §4 that contradicts what `backlog.py` reads; hygiene red on a file you cannot allow without a new reason row; a test of today's behaviour that must change. A stop is a result.

## 4. Report (at most ten lines)

The branch and sha; each act's commit; the gate's id and its code from its line; the suite's counts; the NICE rows kept (ids, levels, one line each); anything left over, and if you stopped, the exact resume line.
