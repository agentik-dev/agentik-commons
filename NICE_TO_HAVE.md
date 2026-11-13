# Nice to have

Findings that block nothing, one row each, in hq design/05 §2's table; `scripts/recordlint` holds it. The list before 2026-11-01 is frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet that touches an area greps them by path.

## Open

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|

## From packet c3

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n2 | S4 | `scripts/recordlint` | a near-miss header is skipped in HANDOFF as in NICE (`status` for `state`, a NICE of four cells), rule 1 as written, so a botched conversion passes; a header opening `#` or `id` could be held instead | design/05 §4 rule 1; `tests/test_recordlint.py`, the skip test's NICE | 2026-11-01, c3's builder; HANDOFF named by c3's refuter round 1 |
| n3 | S4 | `scripts/recordlint` | `item` over 80 characters, which the reader trims (`backlog.py:275`), and `id` not `n<k>` (design/05 §2) pass unchecked | design/05 §2 | 2026-11-01, c3's builder |
| n5 | S4 | `scripts/recordlint` | a `<br>` or a list inside a cell passes unchecked, though GUIDE §9's Cells rule is one line, no list, no `<br>` | `GUIDE.md:75` | 2026-11-01, c3's refuter round 1 |
| n6 | S4 | `scripts/recordlint` | bullets above the first `##` pass, rule 2 holding only the lines under a `##`, though design/05 §2's shape is a title and one head paragraph | `GUIDE.md:75`; `scripts/recordlint:171` | 2026-11-01, c3's refuter round 1 |

## From packet h1 (commit range)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n8 | S4 | `scripts/hygiene` | `--commits` never reads a merge's diff (R7), so a line an evil merge adds that neither side holds goes unscanned; `--diff-merges=cc` lines could be scanned once | `design/packets/h1-commit-range.md` R7, §4 | 2026-11-09, packet h1 |
| n9 | S4 | `scripts/hygiene` | `--commits` scans messages, not the author and committer headers, which a push publishes too | `design/packets/h1-commit-range.md` §4 | 2026-11-09, packet h1 |
| n10 | S4 | `scripts/hygiene` | `--commits` misses a term in a UTF-16 file whose first NUL lies past git's 8000-byte binary probe: git diffs it as text, its `+` lines read as UTF-8; the tree scan finds it | the refuter's `p5`: `MISS UTF-16 BOM, first NUL past 8000 exit=0`, the tree scan of the same file `exit=1` | 2026-11-09, h1's refuter round 1, F5 |
| n11 | S4 | `scripts/hygiene` | a NUL in a commit message (an object made with `hash-object --literally`) cuts `%B` at the NUL, so a term after it is not scanned | the refuter's `p10`: `MISS NUL in a message before the term exit=0`, then `cat-file holds the term: True` | 2026-11-09, h1's refuter round 1, F6 |

## From packet h2 (binary, empty list)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n12 | S4 | `scripts/hygiene` | a private term under an encoding inside a binary (UTF-16, base64, deflate, zip, PDF) is not found, nor a non-ASCII term a 1 MiB cut splits; the range cuts each blob over 1 MiB, the tree a file over 4 MiB; a term in a 4 KiB overlap counts twice | packet h2 ruling 6, its refuter's F4 (`p3_split.py`); `stream_fh`'s cut | 2026-11-10, packet h2 |
| n14 | S4 | `scripts/hygiene` | `re`'s compile cache gives a private row equal to a built-in group's joined pattern the built-in's object, so `GENERIC`'s identity test reads it as built-in and it skips a binary; mark private rows by index instead | the refuter's `p4_identity_anchor.py`: `netpriv` misses net.bin, `netcopy` hits | 2026-11-10, h2's refuter round 1, F3 |
| n15 | S4 | `scripts/plugin-description-bytes` | counts descriptions only; Claude Code lists an agent as `- plugin:name: desc (Tools: ...)`, so the agents plugin's 777 B load as 1,096 B (+319), about 1,350 B in all vs the gate's 1,001; count prefix and suffix, or say in GUIDE §1 it counts descriptions only | listing format read from the Claude Code binary | 2026-11-12, p1 review r1 |
| n16 | S4 | `scripts/plugin-description-bytes` | only `true`/`True`/`TRUE` read as true for `disable-model-invocation`; Claude Code also takes `yes`, `on`, `1` in any case, so a command hidden so is overcounted; a UTF-8 BOM gives `error: no description`, Claude Code's BOM handling unverified | probe: `disable-model-invocation: yes` is listed `10 command yeshidden` | 2026-11-12, p1 review r1 |
| n17 | S4 | `scripts/hygiene` | a private row with an interior wildcard (`a.*b`; a leading or trailing `.*` is stripped) is quadratic on a long newline-free span: a text file's line or a binary's content, which a NUL-padded binary leaves whole; cap the span | `.*` and a term over one line of `a`: 16 KiB 0.6 s, 32 KiB 2.3 s | 2026-11-12, packet h2-hygiene-binary |
| n18 | S4 | `scripts/hygiene` | `unwild` (`:242`) keeps a DOTALL row whole, though a stripped edge `.*` matches the same there too: `(?s).*zqterm`, `.+zqterm`, `.*?zqterm` stay quadratic on a binary; strip under DOTALL too, `.+` and `.*?` with n17 | 64 KiB NUL binary at `2e2431f`: 6.8 s, 7.3 s, 9.0 s, as before the fix | 2026-11-12, h2-hygiene-binary review r2 F1 |
| n19 | S4 | `scripts/plugin-version-check` | the second read takes `refs/heads/main` before `origin/main`, so a stale local main hides the fault: a branch that merged a bumped `origin/main` meets an older merge base, below the merged bump; the newer merge base of the two would close it | a local main behind the bump the branch merged; ruling R1's order | 2026-11-12, packet c7-version-read |
| n20 | S4 | `scripts/plugin-version-check` | under `--json` an exit 2 prints nothing on stdout (R4's unordered version, invalid JSON in the working tree, a numeric version at a base), as the pin's exit-2 paths do, so a caller that parses stdout gets no object; print `{"error": ...}` there too | `main` returns 2 before the `--json` branch (`:234`) | 2026-11-13, c7-version-read review 1 L1 |
| n21 | S4 | `scripts/plugin-version-check` | build metadata is ignored by precedence, so `1.0.0` to `1.0.0+b2` with a change under `plugin/` exits 1 on a branch, though Claude Code refreshes an install on any change to the version string | `precedence` drops `+...`; semver §10 | 2026-11-13, c7-version-read review 1 L3 |
| n22 | S4 | `scripts/plugin-version-check` | the shebang is `#!/usr/bin/env python3`, so the tests run the script under PATH's python3, not the interpreter that runs the tests; the rule for stdlib scripts is `#!/usr/bin/python3` | `:1`; a PATH shim at 3.9.6 and at 3.12 both pass | 2026-11-13, c7-version-read review 1 L4 |
| n23 | S4 | `scripts/plugin-version-check` | R4 runs after the first read, so a branch the pin failed with 1 (an untracked file) and a version not semver-shaped now exits 2, its lines lost; consistent with R4 | the review's probe of an untracked file under a non-semver version | 2026-11-13, c7-version-read review 1 L6 |
| n24 | S4 | `scripts/plugin-version-check` | a path holding a newline breaks "one stderr line a path"; the output is the pin's | the review's odd-name probe | 2026-11-13, c7-version-read review 1 L7 |
