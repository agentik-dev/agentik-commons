# Nice to have: overflow

The oldest S4 rows of `NICE_TO_HAVE.md`, moved here, appended, when that file reaches recordlint's bound. Each row is still open; a packet that touches an area greps it by path.

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
