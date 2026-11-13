# Nice to have

Findings that block nothing, one row each, in hq design/05 §2's table; `scripts/recordlint` holds it. The list before 2026-11-01 is frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet that touches an area greps them by path.

## Open

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n45 | S4 | `plugins/suite` `tools.py` `run_all` | `os.pipe()` sits outside the `try`, so more tools than the process has file descriptors for ends `config` in a traceback; give that tool the `unreadable` row | review 2's lead | 2026-11-13, ak1b review 2 |
| n44 | S4 | `plugins/suite` `tools.py` `run_all` | the group is killed after `proc.poll()` has reaped the process, so where the group is empty its number is free for a moment before the kill; read the exit with `os.waitid(..., WNOWAIT)` and reap after the kill | review 2's lead | 2026-11-13, ak1b review 2 |
| n43 | S4 | `plugins/suite` `messages.md` | the rest of ak1b review 1's words table, for the voice pass: `config.later` as `at the next session`; the `ok` mark on a changed row reads as fine, `note` would read truer; the list's read cell widens the settings column | review 1's words table; build 2's list | 2026-11-13, ak1b review 1 |
| n42 | S4 | `plugins/suite` `fallback.json` | the table's lines (R7, word for word) name `agentik <tool> ...`, which runs only once the door lands; until then `config <tool>` hints at a command that does not exist yet. Ordered after ak2 | review 1's leads | 2026-11-13, ak1b review 1 |
| n41 | S4 | `plugins/suite` `tools.py` `counted_config` | a tool's key holding a blank or a line break shows as an empty key or run together, and no `config <tool>.<key>` reaches it; hold keys to the name pattern or refuse them | review 1's p2 | 2026-11-13, ak1b review 1 |
| n40 | S4 | `plugins/suite` `tools.py` `_keep` | when the cache folder `$XDG_CACHE_HOME/agentik/suite` is a symlink out of the cache root, `_keep` follows it and writes the answer file there | review 1's p6 | 2026-11-13, ak1b review 1 |
| n39 | S3 | `scripts/agentik_install.py` `_door` | it opens whatever is at the door's path, so a FIFO there hangs the install; its no-version line prints the door's raw byte, which can fail under UTF-8. The session's copy opens only a regular file and escapes to ASCII; ak2-door's probe holds both | the session's review of its copy | 2026-11-13, ak1b, from a session review |

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

## From packet ak1a (the suite's command, review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n25 | S4 | `plugins/suite` `cli.py` | `--json` errors: a bad flag with no verb answers `schema: agentik.help/1`, an unknown verb `agentik.usage/1`; `stup --json` gives the remedy `agentik-suite setup`, which itself exits 2 | review 1's L4 | 2026-11-13, ak1a review r1 |
| n26 | S4 | `plugins/suite` `cli.py` | argument edges: `version --version` and `--version --help` are refused as "not a flag here"; `-qh` is refused; an empty argument prints `FAIL   is not a verb`; a 5000-character word is echoed whole | review 1's L5 | 2026-11-13, ak1a review r1 |
| n27 | S4 | `plugins/suite` `cli.py`, `plan.py` | paths: an empty PATH lists the cwd's `agentik-*` as `./agentik-x`; step 6 compares by `normpath`, so a symlinked `~/.local/bin` on PATH reads "not on PATH"; HOME unset reads each path from the cwd; a folder at a launcher's place reads "not placed" | review 1's L6 | 2026-11-13, ak1a review r1 |
| n28 | S4 | `plugins/suite` `plan.py` | corrupt installs, what fix round 1 left: an unreadable manifest plans "no plugin, since the manifest lists none"; a manifest's dependency names are not held to the name rule (`a b`, `x;y` reach a command, quoted); with no dependencies the plan shows five step numbers, not seven | review 1's L7 | 2026-11-13, ak1a review r1 |
| n29 | S4 | `plugins/suite` `cli.py`, `plan.py` | small truths: `help` marks each PATH row `ok` though nothing was checked; step 1's `python3` row is the running interpreter, not a PATH lookup; step 4's waiting row names no command | review 1's L8 | 2026-11-13, ak1a review r1 |
| n30 | S4 | `plugins/suite` `term.py` | a row with something to do shows as `note` (`·`), which reads as information, not as a thing to do; the four state words are the design's, so a change is the design's to make | review 1's note under L9 | 2026-11-13, ak1a review r1 |
| n31 | S4 | `plugins/suite` `plan.py` | no verb places the suite's own launcher yet, so on a real machine step 5 never reads `ok` and the plan ends on the hint that steps 1 to 6 hold no line to run, never on done; it waits for suite's `install-cli` | fix round 1's own run: every `run:` line run in order leaves step 5 `note` | 2026-11-13, ak1a fix r1 |
| n32 | S4 | `plugins/suite` `plan.py` | a launcher left by an uninstalled plugin: step 4 says `not placed; step 3 installs the plugin first`, while steps 5 and 7 print `run:` lines on that same file | the review's states; untrue at 3b7cc56 too | 2026-11-13, ak1a review 2 L3 |
| n33 | S4 | `plugins/suite` `term.py` | a control character in an `installPath`: R6 strips a tab, so its `run:` line names no file (`sh -c` exits 127); U+202E passes, being neither C0 nor C1 | the review's stream probe | 2026-11-13, ak1a review 2 L5 |
| n34 | S4 | `plugins/suite` `catalogue.py`, `term.py` | a capital in a catalogue id stops every verb with `cannot read .../messages.md`, exit 2, though the file is readable and malformed; under `--json` the line is on stderr and stdout is empty; an empty catalogue is a `KeyError` traceback | the review's catalogue probe | 2026-11-13, ak1a review 2 L6 |
| n35 | S4 | `plugins/suite` `cli.py` | an unparseable manifest: `--version` is one line, exit 2, but `help` prints `0.0.0-unknown` and `setup --dry-run` plans no plugin; R9 covers the version verb only | the review's manifest probe | 2026-11-13, ak1a review 2 L7 |
| n36 | S4 | `plugins/suite` `term.py` | at 40 columns each moved detail starts at column 40 of 40, so every row is followed by a line that looks blank; nothing is cut | a pty 40 columns wide, fresh home | 2026-11-13, ak1a review 2 L8 |
| n37 | S4 | `plugins/suite` `plan.py` | a placed launcher with mode 0644 reads `ok` at step 4, and its doctor line cannot run; read the same at 3b7cc56 | the review's states | 2026-11-13, ak1a review 2 L9 |
| n38 | S4 | `plugins/suite` `messages.md` | the table of words' rest: `hint.setup.done` as `setup is done`, `hint.setup.todo` and `hint.setup.blocked` with `run` before the command, `err.setup.plan_only` result first, and term's missing-catalogue line naming the reinstall command | review 2's table of words; its two step 5 and rest lines are built (M3) | 2026-11-13, ak1a review 2 |
