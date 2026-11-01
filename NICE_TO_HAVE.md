# Nice to have

Findings that block nothing, one row each, in hq design/05 §2's table; `scripts/recordlint` holds it. The list before 2026-11-01 is frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet that touches an area greps them by path.

## Open

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n1 | S3 | `scripts/marketplace-versions` | each marketplace `version` line compared with its plugin.json on the remote's main, not only the local checkout; needs the network, not built | `scripts/marketplace-versions:14`, "Nothing is fetched"; the archive's line 13 | 2026-10-14, a plugin changed under an old version; open on main 2026-11-01, c3 |

## From packet c3

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n2 | S4 | `scripts/recordlint` | a file whose only table has a near-miss header (`status` for `state`) is skipped, rule 1 as written, so a botched conversion passes; a header opening `#` or `id` could be held instead | design/05 §4 rule 1; `tests/test_recordlint.py`, the skip test | 2026-11-01, c3's builder |
| n3 | S4 | `scripts/recordlint` | not checked: `item` over 80 characters, which the reader trims (`backlog.py:275`), and `id` as `n<k>` (design/05 §2) | design/05 §2 | 2026-11-01, c3's builder |
