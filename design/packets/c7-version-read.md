# Packet c7: the version check reads what the branch changed, not only the first-parent line

| item | value |
|---|---|
| from | agentik-hq's brief c7 of 2026-11-12, rulings R1 to R5; GUIDE §7 (a change under `plugin/` bumps the version); packet version-check |
| pin | agentik-commons main 6344a9e; worktree `.claude/worktrees/c7-version-read`, branch `c7-version-read` |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; tests build temp repos only, a clone over `file://` of a temp repo, no network |
| may touch | `scripts/plugin-version-check`; `tests/test_version_check.py` (a new class; the eleven tests unchanged); the script's row in `README.md`; `NICE_TO_HAVE.md`; this packet; `history/sittings/2026-11-12-3.md`, and for section 5's fix `history/sittings/2026-11-13-1.md` |
| acceptance | 1 to 10 below, each a test of `BranchReadTest`; `python3 -m unittest tests.test_version_check tests.test_sync` OK; verify green |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id> --strict --timeout 540` in the foreground until the job's line prints |
| budget | a commit per act by explicit path, the packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The fault at the pin

The check finds `since`, the last first-parent commit that moved the version, and lists what changed after it. A branch that adds `plugin/lib/row.py`, never bumps, then merges a main that bumped to alpha.2 gets `since` = its own merge commit (the merge moved the version on the branch's first-parent line): exit 0, "nothing under plugin/ changed since". Landed with `--no-ff`, main's `since` is main's bump and the merge brings `row.py` in: main exits 1. A landing's check runs on the branch, so it lands green and leaves main red.

## 2. Rulings

1. R1, the second read. After today's read, the merge base of HEAD with `refs/heads/main`, else with `refs/remotes/origin/main` (the first ref that resolves and yields a merge base). Its paths: those under `plugin/` that differ from the merge base to HEAD, plus the uncommitted ones today's read lists, less the manifest. When any is listed, the working tree's version must be strictly above the merge base's version by semver precedence (numeric parts by number, a release above its pre-releases, build metadata ignored); not above: exit 1. A bump in flight counts as the version.
2. R2, the lines. On 1, one stderr line a path the second read alone flags: `plugin-version-check: <path>: changed on this branch since its merge base with main (<sha12>, version <its version>); version <v> is not above it: bump plugin.json's version`; a path today's read flags keeps today's line, so what the pin caught prints as at the pin. On 0 where versions were compared, the stdout line ends `; above <its version> at the merge base with main`. `--json` gains `base`, `{"ref", "merge_base", "version", "changed"}`; `version`, `since` and `changed` keep their meaning.
3. R3, where it does not run. Merge base equal to HEAD (main, a detached main, a branch not yet moved) or no commit yet: nothing of the branch's own, the pin's output byte for byte, `--json` included (no `base` key: the eleven tests hold the pin's object). Neither ref, no merge base (an orphan) or a shallow clone that lacks it: `base` null, the exit today's read's alone, never 2 for the missing history, and on 0 the line ends `; no merge base with main, the branch's own changes not read`. No manifest (or no `version` key) at the merge base: any version is above it, no clause, `base.version` null.
4. R4. A path listed and either version not semver-shaped (a non-string included): exit 2, one stderr line naming both, nothing on stdout.
5. R5. A branch behind main that bumped above its own merge base passes, whatever main's number. The eleven tests unchanged; stdlib only; the shebang kept. No new flag.

## 3. Acceptance (`tests/test_version_check.py`, class `BranchReadTest`)

| # | line | 6344a9e |
|---|---|---|
| 1 | the fault's branch: exit 1, the path, both versions; `--json` holds `base` | exit 0, "nothing under plugin/ changed since", no `base` |
| 2 | that branch above main's, uncommitted then committed: exit 0, R2's clause; precedence table (alpha.10 above alpha.2, a release above alpha, build metadata ignored) | exit 0, no clause |
| 3 | main after the `--no-ff` landing: exit 1, today's line | the same (passes) |
| 4 | a branch behind main, bumped above its merge base, under main's: exit 0 | exit 0, no clause |
| 5 | a branch changing nothing under `plugin/` that merges a bumped main: the pin's line | the same (passes) |
| 6 | main, detached at main: the pin's output and `--json` byte for byte; detached at 1's tip: exit 1 | main as wanted; the tip exit 0 |
| 7 | shallow clones (single and `--no-single-branch`), an orphan, a repo of `trunk` alone: today's exit, R3's clause, `base` null | today's exit, no clause, no key |
| 8 | a branch adding `plugin/` over a merge base with no manifest: exit 0 | exit 0, no key |
| 9 | R4: exit 2, one line, on the branch's side and the base's | exit 0 |
| 10 | `refs/remotes/origin/main` when `main` is absent | no key |

## 4. The landing

The vendored copies in the plugin repos are the coordinator's sync round after this lands. GUIDE §7's new sentence is given in the hand-back, not written here.

## 5. The fix of review 1

Review 1 found that in a criss-cross, where HEAD has two merge bases with main, the one base `git merge-base` prints is the one with the newer commit date, so the result turned on dates. F1: main merges the branch's B1 and bumps, the branch merges main's earlier bump M1 and never bumps; red when git picks M1, green when it picks B1. F2: as F1 with one more unbumped path on the branch; green when git picks B1, and the landing leaves main red, the row's own fault.

The ruling, for this fix:

1. R1. The second read takes every base `git merge-base --all` prints, each read as section 2's R1 reads the one. The check is red when any base fails, and each stderr line names the base it fails at (the highest such base, in R2's wording). With one base, every output is byte for byte what 31fa9ad printed.
2. R2. On 0 with more than one base, the clause names the highest version among the bases that compared. `--json`'s `base` is that base (with no comparison, the lowest sha); `bases`, every base's object in sha order, appears only when there is more than one. A base with no version is below any version; a version that cannot be ordered at a base that lists a path is R4's exit 2.
3. R3. F1's branch is red, against section 2's R5 for this one shape, and its mend is a bump on the branch: no landing here makes a criss-cross, since a landed branch is deleted, and a false red costs a bump where a false green leaves main red.
4. R4. Every git call takes `--no-optional-locks`, so the check never rewrites `.git/index` (review 1's L2).
5. The docstring says exit 2 does not apply at a base with no version (L5); the README row names the `origin/main` fallback (L8). L1, L3, L4, L6 and L7 are rows n20 to n24 of `NICE_TO_HAVE.md`.

| # | line (`CrissCrossTest`, `ReadOnlyTest`; both commit-date orders) | 31fa9ad |
|---|---|---|
| 11 | F2's branch: exit 1, `plugin/b.md` and `plugin/c.md` named against M1 | exit 0 in one order |
| 12 | F1's branch: exit 1, the same line in both orders | 1 in one order, 0 in the other |
| 13 | F1's branch bumped above both bases: exit 0, the clause naming 1.1.0; `--json` holds `bases`, two objects | no `bases`; the clause names the base git printed |
| 14 | `BranchReadTest` unchanged and green; a one-base branch's `--json` holds no `bases` | green |
| 15 | a run with a bump in flight leaves `.git/index` byte for byte | the index is rewritten |
