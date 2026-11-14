# Nice to have: overflow

The oldest S4 rows of `NICE_TO_HAVE.md`, moved here whole when the file passes its byte bound (`scripts/recordlint`), appended, never edited.

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
| n32 | S4 | `plugins/suite` `plan.py` | a launcher left by an uninstalled plugin: step 4 says `not placed; step 3 installs the plugin first`, while steps 5 and 7 print `run:` lines on that same file | the review's states; untrue at 3b7cc56 too | 2026-11-13, ak1a review 2 L3 |
| n33 | S4 | `plugins/suite` `term.py` | a control character in an `installPath`: R6 strips a tab, so its `run:` line names no file (`sh -c` exits 127); U+202E passes, being neither C0 nor C1 | the review's stream probe | 2026-11-13, ak1a review 2 L5 |
| n34 | S4 | `plugins/suite` `catalogue.py`, `term.py` | a capital in a catalogue id stops every verb with `cannot read .../messages.md`, exit 2, though the file is readable and malformed; under `--json` the line is on stderr and stdout is empty; an empty catalogue is a `KeyError` traceback | the review's catalogue probe | 2026-11-13, ak1a review 2 L6 |
| n35 | S4 | `plugins/suite` `cli.py` | an unparseable manifest: `--version` is one line, exit 2, but `help` prints `0.0.0-unknown` and `setup --dry-run` plans no plugin; R9 covers the version verb only | the review's manifest probe | 2026-11-13, ak1a review 2 L7 |
| n36 | S4 | `plugins/suite` `term.py` | at 40 columns each moved detail starts at column 40 of 40, so every row is followed by a line that looks blank; nothing is cut | a pty 40 columns wide, fresh home | 2026-11-13, ak1a review 2 L8 |
| n37 | S4 | `plugins/suite` `plan.py` | a placed launcher with mode 0644 reads `ok` at step 4, and its doctor line cannot run; read the same at 3b7cc56 | the review's states | 2026-11-13, ak1a review 2 L9 |
| n38 | S4 | `plugins/suite` `messages.md` | the table of words' rest: `hint.setup.done` as `setup is done`, `hint.setup.todo` and `hint.setup.blocked` with `run` before the command, `err.setup.plan_only` result first, and term's missing-catalogue line naming the reinstall command | review 2's table of words; its two step 5 and rest lines are built (M3) | 2026-11-13, ak1a review 2 |

## From packet ak1b (`config`, reviews 1 and 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n40 | S4 | `plugins/suite` `tools.py` `_keep` | when the cache folder `$XDG_CACHE_HOME/agentik/suite` is a symlink out of the cache root, `_keep` follows it and writes the answer file there | review 1's p6 | 2026-11-13, ak1b review 1 |
| n41 | S4 | `plugins/suite` `tools.py` `counted_config` | a tool's key holding a blank or a line break shows as an empty key or run together, and no `config <tool>.<key>` reaches it; hold keys to the name pattern or refuse them | review 1's p2 | 2026-11-13, ak1b review 1 |
| n42 | S4 | `plugins/suite` `fallback.json` | the table's lines (R7, word for word) name `agentik <tool> ...`, which runs only once the door lands; until then `config <tool>` hints at a command that does not exist yet. Ordered after ak2 | review 1's leads | 2026-11-13, ak1b review 1 |
| n43 | S4 | `plugins/suite` `messages.md` | the rest of ak1b review 1's words table, for the voice pass: `config.later` as `at the next session`; the `ok` mark on a changed row reads as fine, `note` would read truer; the list's read cell widens the settings column | review 1's words table; build 2's list | 2026-11-13, ak1b review 1 |
| n44 | S4 | `plugins/suite` `tools.py` `run_all` | the group is killed after `proc.poll()` has reaped the process, so where the group is empty its number is free for a moment before the kill; read the exit with `os.waitid(..., WNOWAIT)` and reap after the kill | review 2's lead | 2026-11-13, ak1b review 2 |
| n45 | S4 | `plugins/suite` `tools.py` `run_all` | `os.pipe()` sits outside the `try`, so more tools than the process has file descriptors for ends `config` in a traceback; give that tool the `unreadable` row | review 2's lead | 2026-11-13, ak1b review 2 |

## From packet ak2 (the door's writers)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n48 | S4 | `scripts/door-probe` `main` | `--code ""` is taken as no flag and falls back to `AGENTIK_CODE` or the folder above the main checkout, where exit 2 for usage was expected | read only, not run | 2026-11-13, ak2 review 1 L1 |
| n49 | S4 | `scripts/door-probe` `make_lines` | a `$(shell ...)` in a clone's makefile runs when `make -n` reads it, and GNU make remakes an included makefile even under `-n`; the brief's `make -n` design allows both, so a writer's makefile can still run a command during the scan | read only; neither reproduced alone | 2026-11-13, ak2 review 1 L2 |
| n50 | S4 | `plugins/suite` `tools.py` | `agentik-suite <typo>` now reads `known_marketplaces.json`, the marketplace file and `installed_plugins.json` before it answers; a FIFO at one of those paths would hang the answer for an unknown word | read only, not reproduced | 2026-11-13, ak2 review 1 L4 |
| n51 | S4 | `scripts/door-probe` `cases` | for a careful writer that never overwrites an existing door, `race` reads `1 of 1 rounds ended below 0.9.0`, the expected note, which a reader could take for a fault | the probe's run over made-up checkouts | 2026-11-13, ak2 review 1 L7 |
| n52 | S4 | `tests/test_agentik_suite.py` `WallTest` | `test_f2_twenty_slow_tools_add_nothing_past_the_wall` holds a 3.0 s bound that a loaded machine misses by a few ms: it read 3.005 s with three other gate jobs running, and the same commit passed on the next run | gate job `20261113-045824-1435` exit 2, then `20261113-050930-1439` exit 0, both on one commit | 2026-11-13, ak2 build 2 |

## From packet su1 (reviews 1 and 2) and ak2 (review 3)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n53 | S4 | `plugins/suite` `status.py` `matches` | the program is compared by basename, so `match: /opt/bin/lampd watch` finds another folder's `lampd watch`; a `match` whose program is itself a wrapper (`python3 -m lampd`) never matches and always reads missing | review 1's L3 | 2026-11-13, su1 review 1 |
| n54 | S4 | `plugins/suite` `status.py` `_names` | a head that is a link is resolved only when it is absolute; ps shows argv[0] as given, so a bare `oldlamp` linked to `lampd` reads missing | review 1's L4 | 2026-11-13, su1 review 1 |
| n55 | S4 | `plugins/suite` `cli.py` | `status --check --ps` with no value prints `--ps is not a flag here`, which misleads; `--ps --json` takes `--json` as the file's name (the next word is always the value) | review 1's L7 | 2026-11-13, su1 review 1 |
| n56 | S4 | `plugins/suite` `status.py` `beat` | an `at` in milliseconds counts as a beat in the future, so a stale one reads fresh for ever (running) and a missing watcher prints a `since` in year 55840; both follow R6 and R7, and a bound on a beat's future skew would catch it | review 1's L8 | 2026-11-13, su1 review 1 |
| n57 | S4 | `plugins/suite` `status.py` `matches` | `env -C DIR prog` and `env -S "..."` are read as plain flags, so `-C`'s folder or `-S`'s string is taken for the program and such a watcher reads missing: a false alarm, never a false running | `status.matches` by hand: `env -C /tmp lampd watch` reads no match, its head the folder | 2026-11-13, su1 review 2 |
| n58 | S4 | `scripts/door-probe` `rules` | a conditional line (`ifeq`, `else`, `endif`) inside a recipe ends the rule, so a `+` line after it in the same recipe is not read and `make -n` would run it; read a conditional inside a reached rule as `unread` | read only, not reproduced | 2026-11-13, ak2 review 3 |

## From packet ak3p (the join of ak2b-reach, ak3-setup and ak3d-doctor)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n59 | S4 | `scripts/agentik_install.py` `_ascii` | control bytes below 0x20 and 0x7f pass as ASCII, so a VERSION holding an escape sequence reaches the terminal raw through the vendored `install_cli`; the suite verb strips it in `term`; escape them too | ak2b review 1's R1-F3 | 2026-11-13, ak2b review 1 |
| n60 | S4 | `scripts/agentik_install.py` `install` | `install-cli --dry-run --prefix P` says it would place the command where the real run fails (`P` a file: Not a directory); check that the nearest folder above `P/bin` is one it can write to | ak2b review 1's R1-F7 | 2026-11-13, ak2b review 1 |
| n61 | S4 | `plugins/suite` `plan.py` step 5 | in a frozen tree the step's command runs the tree's runner bare, without `-I` or the bytecode prefix, so it writes `~/Library/Caches/com.apple.python` and reads PYTHONPATH; name `<prefix>/bin/<tool>` when that launcher's tree is this lib | ak2b review 1's R1-F9 | 2026-11-13, ak2b review 1 |
| n62 | S4 | `scripts/agentik_install.py` `on_path` | a PATH entry that reaches the prefix's `bin` through a link reads off PATH, so the `export PATH` hint shows when it is not needed; compare `realpath` too | ak2b review 1's R1-F10 | 2026-11-13, ak2b review 1 |
| n63 | S4 | `scripts/agentik_install.py` `install` | a second run replaces the launcher with the same bytes, a new inode and mtime; skip the replace when the bytes are equal | ak2b review 1's R1-F11: a snapshot diff of two runs | 2026-11-13, ak2b review 1 |
| n64 | S4 | `plugins/suite` `cli.py` help | `help install-cli` has no `--prefix` row and `flag.prefix` sits unused in the catalogue; a `VERB_FLAGS` row for it, or help that lists the value flags | ak2b review 1's R1-F13 | 2026-11-13, ak2b review 1 |
| n65 | S4 | `plugins/suite` `install.py` | the prune's line is the module's raw English, not a catalogue line, and `--json` has no `pruned` key, so a failed prune is lost there | ak2b review 1's R1-F14 | 2026-11-13, ak2b review 1 |
| n66 | S4 | `plugins/suite` `cli.py` `parse` | `install-cli --prefix=-x` is refused as no folder though the `=` form gives the value plainly; test the leading `-` only when the value came from the next word | ak2b review 2's N1; `--prefix ./-x` works | 2026-11-13, ak2b review 2 |
| n67 | S4 | `plugins/suite` `cli.py` | `setup --dry-run --prefix` answers `--prefix is not a flag here`, true and unhelpful beside install-cli's own line; rides the `help install-cli` row above | ak2b review 2's N2 | 2026-11-13, ak2b review 2 |
| n68 | S4 | `plugins/suite` `apply.py` gate list | a gate line with an inline ` # comment`, another case (`Settings.json`), a folder (`~/.claude/`) or `$HOME/...` does not name the settings file, so setup goes ahead; strip a trailing comment and compare case-insensitively on darwin | ak3-setup review 1's R1-F5; follows R6's wording | 2026-11-13, ak3-setup review 1 |
| n69 | S4 | `plugins/suite` `apply.py` | a command killed by a signal reads as a negative exit (`exit -9`) in the text and in `--json`; give the signal's name or `128+n` | ak3-setup review 1's R1-F6 | 2026-11-13, ak3-setup review 1 |
| n70 | S4 | `plugins/suite` `apply.py` `execute` | a command that exits 0 but leaves a child holding stdout is held to the wall (600 s for `claude`) and then reads failed; a daemon that leaves the group lives on; whether the real `claude` does this is not known | ak3-setup review 1's R1-F7, not seen with the real `claude` | 2026-11-13, ak3-setup review 1 |
| n71 | S4 | `plugins/suite` `apply.py` | no lock: two setups at once each run every command and each claims the other's writes; an exclusive `flock` beside the journal for the run | ak3-setup review 1's R1-F8: two runs, every call twice | 2026-11-13, ak3-setup review 1 |
| n72 | S4 | `plugins/suite` `apply.py` `--json` | a refusal (`needs_yes`, `gated`, `blocked`, `declined`) prints the error object alone, without `steps`, `ran`, `wrote`, `nothing`, `journal`, which a failed step keeps | ak3-setup review 1's R1-F9; the builder's choice | 2026-11-13, ak3-setup review 1 |
| n73 | S4 | `plugins/suite` `apply.py` `run` | an interrupt after `execute` returns and before `current` clears records a finished command as stopped; one inside `record` reads between steps and can leave it out of `ran` | ak3-setup review 2's N1, not confirmed | 2026-11-13, ak3-setup review 2 |
| n74 | S4 | `plugins/suite` `apply.py` | SIGTERM ends setup with exit 130, SIGINT's code; a caller's script expects 143 | ak3-setup review 2's N2 | 2026-11-13, ak3-setup review 2 |
| n75 | S4 | `plugins/suite` `apply.py` `run` | after the first interrupt both signals stay ignored until `run` returns, so a second Ctrl-C cannot end a last `plan.build` that hangs; whether each read there has its own bound is not checked | ak3-setup review 2's N3 | 2026-11-13, ak3-setup review 2 |
| n77 | S4 | `plugins/suite` `doctor.py` `own_doctors` | doctor runs `<exe> doctor` for an `agentik-<verb>` it has just flagged as a shadow; leave out a word that is a verb or reserved | ak3d review 1's R1-F3 | 2026-11-13, ak3d review 1 |
| n78 | S4 | `plugins/suite` `doctor.py` `shadow` | an `agentik-help` on PATH reads as a shadow `fail`, exit 1, though the door answers `help` before any lookup; leave `help` out of the shadow words | ak3d review 1's R1-F4 | 2026-11-13, ak3d review 1 |
| n79 | S4 | `plugins/suite` `doctor.py` hint | when only a fail with no remedy is left (a shadow, a settings fault), the closing hint still says to run each `run:` line above, and there is none | ak3d review 1's R1-F5; follows R5 | 2026-11-13, ak3d review 1 |
| n80 | S4 | `plugins/suite` `doctor.py` | a tool's doctor killed by a signal reads `its doctor exits -9 and prints nothing`; a line for a negative code | ak3d review 1's R1-F6 | 2026-11-13, ak3d review 1 |
| n81 | S4 | `plugins/suite` `doctor.py` `_last_line` | a tool's last line has no length bound: a 900,000-character line is the detail in the text and in `--json`; cut it near 200 characters | ak3d review 1's R1-F7: 902,737 bytes out | 2026-11-13, ak3d review 1 |
