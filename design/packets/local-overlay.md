# Packet local-overlay: a local overlay for the owner's marketplace

| item | value |
|---|---|
| from | agentik-r1 §5.2 (the marketplace; D1, the owner's machine); GUIDE §2 (the one marketplace, `make local-marketplace`), §6 (no private repo in a tracked file; the private list kept outside the repos), §9 (this shape); the hq sitting's ruling of 2026-10-17 (reversible): a plugin whose repo is not public reaches the owner's machine through a local overlay, and the published file names public repos only; the code at e6d9e16 |
| pin | `main` at e6d9e16; branch `local-overlay`, worktree `.claude/worktrees/local-overlay` |
| wall | this repo only. No push, merge, `--amend` or rebase; no network; no `claude plugin` command; no install. Never read or write `~/.config/agentik/` or `~/.local/share/agentik/`: every test passes `AGENTIK_MARKETPLACE_DIR` and `AGENTIK_MARKETPLACE_OVERLAY` under a temp dir. Never build a relay binary or run any relay verb. One `make` at a time, started only once `ps -axo command \| grep -E '(^\|/)make( \|$)' \| grep -v grep` prints nothing |
| may touch | `scripts/marketplace-check`, `Makefile`, `tests/test_marketplace.py`, `scripts/local-marketplace` (new, only if the merge moves out of the Makefile: builder's call, logged), `README.md` (the marketplace row and the `make local-marketplace` line), `GUIDE.md` (§2's last sentence), `NICE_TO_HAVE.md` (new lines at the end only), this packet, `history/sittings/*.md`, `history/sessions/NEXT` |
| acceptance | 1: `python3 -m unittest -v tests.test_marketplace -k overlay -k extra 2>&1 \| grep -c ' \.\.\. ok$'` reads 6 (main: 0; 4 at the cut, 6 after fix round 1's two tests); 2: `python3 -m unittest tests.test_marketplace 2>&1 \| tail -1` reads `OK`; 3: `make -n local-marketplace \| grep -c 'marketplace-local.json'` reads 1 (main: 0); 4: `scripts/marketplace-check >/dev/null; echo $?` reads 0; 5: `git diff main -U0 \| grep '^+' \| grep -ci 'obs[e]rver'` reads 0; 6: `git status --short \| wc -l` reads 0 |
| verify | `make check`, in the worktree, by the builder after the last act and by the coordinator after merging |
| budget | acts: 0 this packet; 1 `marketplace-check --local` takes further entries, its tests; 2 the overlay in `make local-marketplace`, its tests; 3 README, GUIDE, `make help`, then `make check`. 60 turns, 120k context; one commit per act; checkpoint at 80% |

## 1. What the source says

- **The published file (agentik-r1 §5.2).** `.claude-plugin/marketplace.json` lists the five tools, each `{"source": "git-subdir", "url": "https://github.com/agentik-dev/agentik-<tool>.git", "path": "plugin"}`; `scripts/marketplace-check` holds it to exactly those five.
- **The owner's machine (D1).** `make local-marketplace` writes the same file with `file://<AGENTIK_CODE>/agentik-<name>` urls into `$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json` and checks it with `marketplace-check --local`, which today also demands exactly the five.
- **The gap.** A plugin whose repo is not public cannot sit in the published file: an install fails for anyone without access, and GUIDE §6 bars a private repo's name from any tracked file here. The owner still installs it as `<name>@agentik`.

## 2. Rulings

1. **The overlay.** A make variable `AGENTIK_MARKETPLACE_OVERLAY ?= $(HOME)/.config/agentik/marketplace-local.json`, beside the hygiene private list. The file is a JSON object whose `plugins` is a list of entries in the published form (https url, `path` `plugin`, `description`, `version`), so an entry moves to the published file unchanged once its repo is public.
2. **The merge.** `make local-marketplace` appends the overlay's entries after the published five, in the overlay's order, then rewrites every url to `file://` as today and runs `marketplace-check --local` on the result. An absent overlay file: the output is today's, byte for byte. An unreadable overlay, one that is not JSON, or one with no `plugins` list: the target fails and writes nothing new.
3. **`--local` takes further entries.** Under `--local`, the five are still required; any further entry is held to the same shape as theirs: a name matching `[a-z][a-z0-9]*(-[a-z0-9]+)*`, each name once (an overlay that repeats one of the five fails), `git-subdir`, a `file://` url whose last segment is `agentik-<name>`, `path` `plugin`, a semver `version`. The valid line counts the entries found. Without `--local` nothing changes: exactly the five, public urls.
4. **Tests own their inputs.** Every `make local-marketplace` in a test passes both variables under its temp dir, so the owner's overlay never reaches a test. Four new tests carry `overlay` or `extra` in their names: an absent overlay leaves the output as today's; an overlay of one entry `extra` gives six entries, the sixth `file://<code>/agentik-extra`, the five unchanged; an overlay naming `session` fails the target; `--local` accepts an extra entry of the right shape and refuses one with an https url or a `path` other than `plugin`.
5. **Words.** GUIDE §2's last sentence gains the overlay in one clause; README's marketplace row and `make local-marketplace` line say the published file names public repos only and the local file adds the overlay's; `make help` names `AGENTIK_MARKETPLACE_OVERLAY`; `marketplace-check`'s docstring says what `--local` accepts.
6. **Out.** `marketplace-versions` reads the published file only and stays so; comparing an overlay entry with its checkout is a NICE line.

## 3. Interfaces

| item | contract |
|---|---|
| `make local-marketplace` | as today, plus the overlay's entries (ruling 2); exit 0 written and checked, non-zero otherwise |
| `scripts/marketplace-check --local [FILE]` | exit 0 the five plus any well-formed further entries, 1 a check said no (one stderr line each), 2 usage or no readable file |
| `scripts/marketplace-check [FILE]` | unchanged |

## 4. Findings that name this row

None open. Any finding goes to the end of NICE_TO_HAVE.md.

## 5. Forbidden reads

Any transcript, any state folder, `~/.config/agentik/` (the private list and the overlay), `~/.local/share/agentik/`, and from a test any real tool checkout.

## 6. Report

The branch head, the commits, the test count, the six acceptance lines, the `make check` result, each choice beyond §2 in one sentence, and anything left for NICE_TO_HAVE.md.
