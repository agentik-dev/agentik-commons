# Packet sy4-sync-check: `scripts/sync --check <repo>` says which vendored copies are behind commons, and writes nothing

| item | value |
|---|---|
| from | agentik-hq's brief sy4-sync-check of 2026-11-20, R1 to R6, on the row's design D1 (an advisor's pick from a read of the suite for design defects); level S3 |
| pin | agentik-commons main 206dfb4 (suite 0.7.37); worktree `.claude/worktrees/sy4-sync-check`, branch `sy4-sync-check`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no tool synced or written; no test reads the live home or state; made-up names in fixtures |
| may touch | `scripts/sync`, `tests/test_sync.py`, `GUIDE.md` (the sync sentence), `design/packets/sy4-sync-check.md`, `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | `python3 -m unittest tests.test_sync` directly; `make check` once, last, through the gate queue; `scripts/hygiene --require-private` on the tree and on `--commits main..HEAD` |
| acceptance | 1 to 9 below |

## 1. The finding

The owner's words, 2026-11-20: "Put a new Fable advisor to look for design defects in our suite. Look for the best 3 things to do for our repos and then farm them out to Opus workers when it comes back with a decision." The advisor's pick: a tool repo's `scripts/hygiene` had drifted from commons' (203 changed lines in four tools) while every repo's own `shasum -c scripts/vendored.sha256` read green, since that file holds the repo's own hashes. At the pin `scripts/sync` takes one argument and writes; it has no read mode, and `sync --check <repo>` exits 2 as usage.

## 2. Rulings

- R1, one table: one function computes what sync places (source in commons, destination in the repo, mode, listed or seeded once); the write path and the check both read it. The write path's bytes, `vendored.sha256` and exits are the pin's for every shape the tests cover.
- R2, the check: `--check <repo>` creates, changes and removes nothing, a temp file included. Each listed destination that is absent, not a regular file, or differs from commons' bytes or mode is `behind <path>`; `vendored.sha256` lacking a listed path, or naming one sync would not list, is `unlisted <path>`, and a repo with no manifest reads every listed path `unlisted`. Paths from the repo's root, sorted, once each, `behind` before `unlisted`, on stdout; none of either: `sync: <repo>: every copy is commons'`, `<repo>` resolved as the write path names it.
- R3, never compared: the seeded `plugin/lib/agentik-tool.conf` and `plugin/lib/agentik_term/messages.md`.
- R4, exits: 0 every copy is commons'; 1 a `behind` or `unlisted` line; 2 usage and each refusal the write path has, the same stderr, nothing on stdout. `--check` is the only flag; `--check` alone, `--check a b` and any other `-` word are usage.
- R5, the words: the script's header and GUIDE's sync sentence (§6 holds it, not §5 as the brief has it) name the check and its exits. No other record changes.
- R6, what stands: `bin/agentik` and every vendored source's bytes; no tool repo is synced or written.

## 3. Interfaces

- `scripts/sync [--check] <repo>`; usage line `usage: scripts/sync [--check] <repo>`.
- `table` in `scripts/sync`: one line a file, `source destination mode listed`; `source` `:init` is sync's own `__init__.py` text, `:messages` and `:conf` the seeds (`listed` `n`, mode `-`).

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `-k test_check_after_sync_is_clean`: exit 0, the one `every copy` line, plugin and plain fixtures | exit 2, usage |
| 2 | `-k test_check_a_copy_changed_with_its_line`: exit 1, `behind scripts/hygiene` alone | exit 2, usage |
| 3 | `-k test_check_absent_and_unlisted`: removed copy `behind`; removed or extra manifest line `unlisted`; no manifest exit 1; mode alone `behind` | exit 2, usage |
| 4 | `-k test_check_writes_nothing`: bytes, mode, mtime of every file under the fixture and commons as before, none added | exit 2, writes nothing |
| 5 | `-k test_check_skips_the_tools_own`: conf and messages.md edited, exit 0 | exit 2, usage |
| 6 | `-k test_check_usage`: `--check`, `--check a b`, `--bogus <fixture>`, `--check <not a checkout>` exit 2, stdout empty | exit 2 |
| 7 | `python3 -m unittest tests.test_sync`: the pin's 16 tests unchanged | 16 OK |
| 8 | not a test: `scripts/sync --check` against a sibling tool checkout last synced before commons' scanner changed, read only | exit 2, usage |
| 9 | `make check` through the gate queue | green at 206dfb4 |
