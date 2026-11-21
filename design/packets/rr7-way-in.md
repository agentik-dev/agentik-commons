# Packet rr7-way-in: a public repo carries the two pages that say how a stranger gets in

| item | value |
|---|---|
| from | agentik-hq's brief rr7-way-in of 2026-11-20, R1 to R5, on the coordinating repo's design of the records root, item 21, and the owner's answers of 2026-11-19 and 2026-11-20; level S3 |
| pin | agentik-commons main b4b4cc8, cut before hn1-help-next lands, on the coordinator's word (a later phase 2 merges main); worktree `.claude/worktrees/rr7-way-in`, branch `rr7-way-in`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no tool synced or written; no test reads the live home or state; made-up names in fixtures |
| may touch | `templates/CONTRIBUTING.md`, `templates/SECURITY.md`, `CONTRIBUTING.md`, `SECURITY.md`, `scripts/sync`, `tests/test_rr7_way_in.py`, `GUIDE.md` (a new §6 paragraph), `design/packets/rr7-way-in.md`, `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | `python3 -m unittest tests.test_rr7_way_in tests.test_sync` directly; `make check` once, last, through the gate queue; `scripts/hygiene --require-private` on the tree and on `--commits main..HEAD` |
| acceptance | 1 to 8 below |

## 1. The finding

The owner's words. Asked what a stranger's pull request gets (2026-11-19): "Read as an issue". Asked whether the hq may switch on the host's private vulnerability reporting for each public repo (2026-11-20): "The hq does"; it is on. The design's sentence: "An issue is the way in, as designed. A public repo carries `CONTRIBUTING.md` and `SECURITY.md` from one commons template with no name in it. They say: work is planned privately and no roadmap is promised; an issue is answered when it is placed; a security report goes through the host's private report form, never an address in the repo." At the pin no repo of the suite has either page, and `scripts/sync` places none.

## 2. Rulings

- R1, the two templates: `templates/CONTRIBUTING.md` and `templates/SECURITY.md`, the brief's text but one line, review 1's ruling; no org, repo, person, address or link. The brief's "its code, its decisions and its design" is a `sibling` hit (the scanner's `decision[s]`, a sibling tool's name), and five of the seven licensed public repos, commons among them, publish no decision ledger (F1, F3): the page reads "This repo publishes its code and its design."
- R2, the placing: `table()` gives a target whose root holds a regular file `LICENSE` two more rows, `templates/<page> <page> 644 y`, after the seven scripts and before the plugin rows, so the write path places them, `vendored.sha256` lists them and `--check` reads them. A `LICENSE` that is a folder or a symlink is not a regular file: neither page. A plugin with or without `lib/` is the same.
- R3, commons' own: `CONTRIBUTING.md` and `SECURITY.md` at the root, equal to the templates, held so by a test.
- R4, the words: a new paragraph in GUIDE §6 and a header line in `scripts/sync` say the rule. The README source gains nothing.
- R5, what stands: every other table row, `--check`'s other lines, the write path's stdout, and every byte for a target with no `LICENSE`.

## 3. Interfaces

- `table` rows `templates/CONTRIBUTING.md CONTRIBUTING.md 644 y` and `templates/SECURITY.md SECURITY.md 644 y`, under `[ -f "$target/LICENSE" ] && ! [ -L "$target/LICENSE" ]`.
- `place()` takes a destination with no folder: its temp file is in the target's root (at the pin `${2%/*}` of a bare name is the name itself).

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `-k test_a_licensed_target_gets_both_pages`: both at the root, the templates' bytes, mode 644, listed; `--check` exit 0 | neither page |
| 2 | `-k test_check_says_behind_a_page`: one removed, one edited: `behind <page>`, exit 1 | exit 0 |
| 3 | `-k test_no_licence_is_the_pins`: no `LICENSE`, a folder, a symlink: neither page, the pin's manifest and `--check` line | as now |
| 4 | `-k test_commons_own_pages_are_the_templates` | no page |
| 5 | `-k test_the_templates_name_nothing` (no `@`, no `http`, and the scanner on a checkout of the two pages alone exits 0), and `scripts/hygiene --require-private` on the tree and `--commits main..HEAD`: exit 0 | no template; the brief's wording: 1 `sibling` hit |
| 6 | `python3 -m unittest tests.test_sync`: the pin's 22 tests unchanged | 22 OK |
| 7 | not a test: `scripts/sync --check` against a sibling checkout with a `LICENSE` and one without, read only | exit 1 each, no page line |
| 8 | `make check` through the gate queue | green at b4b4cc8 |
