# Packet version-check: a plugin changed under an old version, and the marketplace's version lines

| item | value |
|---|---|
| from | NICE_TO_HAVE "A plugin changed under an old version (2026-10-14), S3" and "agentik-r1-commons, the marketplace's versions"; GUIDE §2 (the marketplace), §5 (`make check`), §6 (the vendored copies, `scripts/sync`), §7 (a change under `plugin/` bumps the version), §9 (this shape) |
| pin | `main` at e59a318; branch `version-check`, worktree `.claude/worktrees/version-check` |
| wall | this repo only; no push, `--amend`, rebase or merge; no network; no `claude plugin` command; no install; never `scripts/sync` against a real repo (its tests use temp repos); never run the relay with any verb, never build a relay binary; tests write in temp dirs only and never read a real tool checkout; one `make` at a time |
| may touch | `scripts/plugin-version-check` (new), `scripts/marketplace-versions` (new), `scripts/sync`, `tests/test_version_check.py` (new), `tests/test_marketplace_versions.py` (new), `tests/test_sync.py`, `Makefile`, `README.md`, `GUIDE.md` (§1, §5, §7, one clause each), `NICE_TO_HAVE.md` (the two lines in `from`), this packet |
| acceptance | 1: `python3 -m unittest tests.test_version_check 2>&1 \| tail -1` reads `OK` (pin: no such module); 2: `python3 -m unittest tests.test_version_check -k since 2>&1 \| tail -1` reads `OK`; 3: `python3 -m unittest tests.test_marketplace_versions 2>&1 \| tail -1` reads `OK` (pin: no such module); 4: `python3 -m unittest tests.test_sync 2>&1 \| tail -1` reads `OK` (pin: passes with three copies, fails on four once the test names the fourth); 5: `scripts/plugin-version-check 2>/dev/null; echo $?` reads `2` (this repo has no `plugin/`); 6: `make -n check \| grep -c -- '--if-complete'` reads `1`; 7: `git status --short \| wc -l` reads `0` |
| verify | `make check`, in the worktree, by the builder after the last act and by the coordinator after merging |
| budget | acts: 0 this packet; 1 `plugin-version-check`, its tests, sync's fourth copy; 2 `marketplace-versions`, its tests, the Makefile; 3 the README, GUIDE and NICE_TO_HAVE text, then `make check`. 100 turns, 150k context; one commit per act; checkpoint at 80% |

## 1. What the source says

- **The bump rule (GUIDE §7).** Any change under a plugin's `plugin/` bumps `plugin.json`'s version, since Claude Code refreshes an installed plugin only on a new version. On 2026-10-14 two plugins had changed under an old version: an update said the install was current while its hooks and a skill differed from the checkout. Both were bumped by hand.
- **The check NICE_TO_HAVE asks for.** Vendored into every plugin repo's `make check`, it fails when `plugin/` changed after the commit that last changed `plugin.json`'s version.
- **The second face (2026-10-16).** The marketplace's own `version` lines can trail the plugins': one entry read alpha.15 while its `plugin.json` was alpha.18. Installs read `plugin.json`, so nothing broke. A local compare of each entry with its checkout's `plugin/.claude-plugin/plugin.json`, with no network, shows the drift.
- **The shared copies (GUIDE §6).** The canonical scripts live here; `scripts/sync <repo>` copies them into `<repo>/scripts/` and writes `scripts/vendored.sha256`, which the repo's `make check` verifies.

## 2. Rulings

1. **The walk.** `git log --first-parent --format=%H -- plugin/.claude-plugin/plugin.json`, newest first; the first commit whose `version` value differs from its first parent's (an absent file or unreadable JSON reads as no value) is `since`. The first-parent line is what the default branch shipped: a merge that brings a bump in moves the version for every change it merges. A file whose version never changed takes its first commit, which the same rule finds.
2. **A bump in flight.** When the working tree's `version` differs from HEAD's (HEAD absent included), the uncommitted bump covers every change: exit 0, `since` null, `changed` empty. Without it, a builder's `make check` before the commit would be red for the fix the check asks for.
3. **The changed set.** `git diff --name-only --no-renames <since> HEAD -- plugin/` plus `git status --porcelain -z --untracked-files=all --no-renames -- plugin/`; ignored files stay out; `plugin.json` counts like any file; paths from the checkout's top level, sorted, once each.
4. **Exit 2.** Usage, not inside a work tree, git missing or failing, or no readable string `version` in the working tree's `plugin.json`.
5. **A sibling script.** The compare is `scripts/marketplace-versions`; `marketplace-check` stays the shape check of one file, whose `--local` already means the `file://` form. Each entry's checkout is `<AGENTIK_CODE>/agentik-<name>`, as `make local-marketplace` has it; `AGENTIK_CODE` defaults to this repo's parent folder. No directory: a note, skipped. A directory with no readable `version`: a line, exit 1. A difference reads `trails`, `leads` or `differs` by semver precedence.
6. **The targets.** `make versions` runs the compare; `make check` runs it under `--if-complete`, which compares only when every entry's checkout is present and otherwise gives one note and exits 0, so a clone of commons alone stays green. `make help` says so.
7. **Vendoring.** `scripts/sync` copies `plugin-version-check` as a fourth file and pins it in `vendored.sha256`. Wiring it into a tool repo's `make check` is that repo's next sync packet; GUIDE §1 and §5 name it.
8. **Out.** NICE_TO_HAVE's compare against the remote's main needs the network, so it stays out.

## 3. Interfaces

| item | contract |
|---|---|
| `scripts/plugin-version-check [--json] [--repo DIR]` | from a plugin repo's root (or `DIR`); exit 0 none changed (one stdout line), 1 one stderr line per changed file, 2 as ruling 4; `--json` prints `{"version": ..., "since": "<sha>" or null, "changed": [...]}` with the same exit |
| `scripts/marketplace-versions [--if-complete] [FILE]` | `FILE` defaults to `.claude-plugin/marketplace.json`; exit 0 every present entry matches (one stdout line, notes on stderr), 1 one stderr line per entry that trails, leads or differs, 2 usage or no readable marketplace |
| `scripts/sync <repo>` | as today, plus `scripts/plugin-version-check`, in `vendored.sha256` |
| `make versions`, `make help` | the compare; the targets, one line each |

## 4. Findings that name this row

The two NICE_TO_HAVE lines in `from`: each gains what landed and what is left (each repo's sync packet, and the remote compare). Every other finding goes to the end of NICE_TO_HAVE.md.

## 5. Forbidden reads

Any transcript, any state folder, the private hygiene list (the scan reads it; never print or copy it), and, from a test, any real tool checkout: every test builds its repos and checkouts in a temp dir.

## 6. Report

The branch head, the two scripts and their exits, the test count, the `make check` result, each choice beyond §2 in one sentence, and anything left for NICE_TO_HAVE.md.
