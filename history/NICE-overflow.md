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
| n82 | S4 | `plugins/suite` `messages.md` | `err.verb.plugin`'s remedy still names `setup --dry-run <word>`, now that `setup <word>` applies | ak3-setup build 1's lead | 2026-11-13, ak3-setup build 1 |
| n83 | S4 | `plugins/suite` `apply.py` failed step | a failed step's line quotes the command's last output line, for a wrapped message a fragment, and adds a period after one: `said and the repository exists.. Mend that`; quote a full line and add no second period | `setup --yes` in a temp HOME behind a network wall, step 2's `marketplace add` | 2026-11-13, ak3p phase 2 |

## From packet sc2-name (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n84 | S4 | `scripts/plugin-launcher` | the launcher exports `AGENTIK_ARGV0` in every tool and only the suite drops it, so other tools' children inherit it, harmless only by the suite's `samefile` check. Closed: GUIDE §10's `AGENTIK_ARGV0` paragraph says so | review 1's N1 | 2026-11-13, sc2 review 1 |
| n85 | S4 | `plugins/suite` `prog.py` `form` | the door form says `agentik` whenever a door at 0.2.0 or newer and any `agentik-suite` are on PATH, so from a newer clone `next: agentik doctor` runs the older suite; per design/23 §3, but may surprise | review 1's N2 | 2026-11-13, sc2 review 1 |
| n86 | S4 | `plugins/suite` `doctor.py` | `"%s doctor" % exe` still writes another tool's name before a verb outside `prog.start`; it runs, since the exe came from PATH, but in the door form reads `agentik-session doctor`, and R1's source test does not see it | review 1's N3: `doctor.py:111` | 2026-11-13, sc2 review 1 |
| n87 | S4 | `plugins/suite` `messages.md` | `next: ... config suite.<key>` is a template: pasted, `sh` reads `<key>` as a redirection and exits 2 (before sc2 too) | review 1's N4: the line pasted into `sh -c` exits 2 | 2026-11-13, sc2 review 1 |

## From packet rp1-shapes (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n88 | S4 | `scripts/hygiene` `secret` | Slack's app-level token (`xapp-1-...`) and refresh token (`xoxe-1-...`) count 0; the configuration token `xoxe.xoxp-...` counts 1; one more pattern | review 1's N1, probe p1 | 2026-11-13, rp1 review 1 |
| n89 | S4 | `scripts/hygiene` `secret` | OpenAI's `sk-svcacct-...`, `sk-admin-...` and `sk-None-...` keys count 0; the brief named the key with and without its project part only | review 1's N2, probe p1 and an in-process check | 2026-11-13, rp1 review 1 |
| n90 | S4 | `scripts/hygiene` `secret` | the AWS key pattern's `\b` misses a key after a JSON `\n` escape, as R1-F1 did for three shapes; `TOKEN_START` is the fix | review 1's N3, in-process at b62ddad and 0af1a76 | 2026-11-13, rp1 review 1 |
| n91 | S4 | `scripts/hygiene` `secret` | random base64 can go red: 134 MB of it gives 3 hits (`AIza`), 134 MB of base64url 47 (4 at the base, `ghp_`); a repo that commits big blobs may go red after the sync | review 1's N4; nine sibling copies found no new hit | 2026-11-13, rp1 review 1 |
| n92 | S4 | `scripts/hygiene` `--json` | none found in matching: keys and exit codes unchanged, `--commits` counts a token in a diff line and a message; binary, UTF-16, oversize and path cases count 1 | review 1's N5 | 2026-11-13, rp1 review 1 |
| n93 | S4 | `scripts/hygiene` | the new shapes may cost 14 to 28 percent of wall time over a 120 MB tree (base 29.9 s and 23.3 s, tip 38.4 s and 26.5 s), noisy under host load; time it on a quiet host | review 1's N6 | 2026-11-13, rp1 review 1 |
| n94 | S4 | `tests/test_agentik_suite.py` | `WallTest` f1, f2, f4 and `ConfigTest.test_a1_a4_three_levels_piped` fail at 3.09 to 3.41 s against a 3.0 s bound under host load, at base and tip alike | review 1's N7 | 2026-11-13, rp1 review 1 |
| n95 | S4 | `design/packets/rp1-shapes.md` | the review's acceptance read: 1 held bare only (R1-F1), 2, 3, 5 and 6 hold, 4 holds with the copy at 100644, 7 rests on the build's gate | review 1's N8 | 2026-11-13, rp1 review 1 |
| n96 | S4 | `scripts/hygiene` JWT | each part opens `eyJ`, three letters where the brief says six, a superset; an unsigned JWT (`header.payload.`, empty signature) counts 0 | review 1's N9 | 2026-11-13, rp1 review 1 |
| n97 | S4 | `scripts/hygiene` | a token split across a line end counts 0, but a project key whose first half is 20 characters or more; the design's item 13 accepts this | review 1's N10 | 2026-11-13, rp1 review 1 |
| n98 | S4 | `scripts/hygiene` `secret` | a lead for rp2: GitLab's `glpat-<body>.01.<suffix>` form counts 1 but the match ends at the first `.`, so a scrub of the match alone leaves the suffix | review 1's N11 | 2026-11-13, rp1 review 1 |
| n99 | S4 | `plugins/suite` `sources.py` `whose` | a `projectPath` of `.` or `""` is read against the process cwd, so it is the repo's from any folder | note 4, p4 S8 | 2026-11-13, fk1 review 1 |
| n100 | S4 | `plugins/suite` `sources.py` `_runs` | an unset or empty PATH reads `.`, so a stray `./agentik-T` runs as `placed`; R6 copies `doctor.first_door` | note 5, p4 S7 | 2026-11-13, fk1 review 1 |
| n101 | S4 | `plugins/suite` `sources.py` `mirror` | an `agentik` source that is no mapping reads `mirror` false; R8 may mean true | note 6 | 2026-11-13, fk1 review 1 |
| n102 | S4 | `plugins/suite` `sources.py` `read` | an entry whose folder is gone stands `found`, where `plan.py` reads it not installed | note 7, read only | 2026-11-13, fk1 review 1 |
| n103 | S4 | `plugins/suite` `sources.py` `entries` | the v1 dict shape of `installed_plugins.json` reads `absent`, as `plan.py` does | note 8 | 2026-11-13, fk1 review 1 |
| n104 | S4 | `plugins/suite` `config.py`, `scripts/voice` | `describe sources T extra` names `describe` alone; a TOOL of `""` or `suite` reads `absent`; voice says `line 0` for an unreadable user file | notes 9, 10 | 2026-11-13, fk1 review 1 |
| n105 | S4 | `plugins/suite` `doctor.py` `read_answer` | one malformed field voids a tool's whole answer, so a `fail` check with no `detail` leads to the second round, and a plain `doctor` that exits 0 reads `its doctor passed`: the fail is hidden (as R1 and R2 rule) | review 1's note: probe p2 `eee` | 2026-11-13, sc10 review 1 |
| n106 | S4 | `plugins/suite` `doctor.py` `read_answer` | the reader is lenient: a check with no `remedy` key is accepted though the contract lists it, and an empty name and detail draw a bare `    FAIL` row | review 1's note: probe p2 `kkk` | 2026-11-13, sc10 review 1 |
| n107 | S4 | `plugins/suite` `doctor.py` | an answer with an empty `checks` list reads `ok  <tool>  0 checks` | review 1's note: probe p2 `jjj` | 2026-11-13, sc10 review 1 |
| n108 | S4 | `plugins/suite` `doctor.py` | more than 1 MiB of stdout in round 1 is one start and the pin's `could not start, or printed more than 1 MiB` warn, with no second round (R2 rules this) | review 1's note | 2026-11-13, sc10 review 1 |
| n109 | S4 | `plugins/suite` `term.py` `clean` | `clean` strips C0, DEL and C1 only: U+202E (right-to-left override) is drawn raw, and the text left by a stripped escape still shows (`ti]0;PWNEDtle`); `--json` escapes U+202E | review 1's note, on a pipe and a pty | 2026-11-13, sc10 review 1 |
| n110 | S4 | `plugins/suite` `doctor.py` | a tool's remedy that holds a newline is flattened into one line and printed as given, so `next:` can show a joined command | review 1's note | 2026-11-13, sc10 review 1 |
| n111 | S4 | `plugins/suite` `term.py` `_cleaned` | `--json` is not a tool's bytes verbatim when they hold control characters: all but `\n` are removed (before sc10) | review 1's note | 2026-11-13, sc10 review 1 |
| n112 | S4 | `plugins/suite` `doctor.py` `close_command` | a settings fault or a shadow `fail` with no other problem closes on `2 failed, 0 to look at, 18 ok.` and no `next:` line (R8's "else none"); the pin ended on a hint | review 1's note: probe p7 | 2026-11-13, sc10 review 1 |
| n113 | S4 | `plugins/suite` `doctor.py` `_rows` | failing step-1 rows fold into one row, `FAIL  prereqs  not on PATH: claude, git` (R6 rules this; each subject is still named) | review 1's note | 2026-11-13, sc10 review 1 |
| n114 | S4 | `plugins/suite` `doctor.py` | when the close is setup (R8 b), a failing tool's own doctor command shows nowhere on the screen; the tool shows only its group line or rows | review 1's note: probe p3 `nodoor` | 2026-11-13, sc10 review 1 |
| n115 | S4 | `plugins/suite` `doctor.py` `_under` | build 1's lead that `fix: <setup>` can show up to three times under a plan's rows (a failing door's install-cli the close) was not reproduced: in an old-door HOME the plan rows were counted as waiting | review 1's note; build 1's charter | 2026-11-13, sc10 review 1 |
| n116 | S4 | `plugins/suite` `doctor` | not run by review 1: a real terminal emulator (bytes on a pty only), a HOME or tool path with spaces, a colour pty run at the pin, a door placed by a real `setup` | review 1's note | 2026-11-13, sc10 review 1 |
| n117 | S4 | `plugins/suite` `messages.md` | `doctor.settings.unchecked` is 79 characters with its slots in, over the 76 of the row's acceptance 9, kept by R9; shorten it when that message is next turned | build 2's charter; acceptance 9's test | 2026-11-13, sc10 phase 2 |
| n118 | S4 | `plugins/suite` `doctor.py` details | the doctor's `doctor.tool.*` detail takes the last line of a tool's own doctor output whole, and the `shadow` and `plan` details hold paths; free by R4 and kept by `gather`, so rp2's scrub is their only guard: a line for rp2's or rp6's review | review 1's first note, read | 2026-11-13, rp3 review 1 |
| n119 | S4 | `gather.py` `_entry` | takes the first install of a key's list, so with several scopes (a project-scoped install first) the version shown may be another folder's; it does not change with the working folder | review 1's note; read, not verified on a real file | 2026-11-13, rp3 review 1 |
| n120 | S4 | `gather.py` `_launcher` | an unreadable launcher (mode 000) reads None, as an absent one does, not `unreadable`: `read_regular` gives None for both | review 1's note; read, not probed | 2026-11-13, rp3 review 1 |
| n121 | S4 | `gather.py` `_installed` | reads `installed_plugins.json` with no size limit (`read_regular`, limit -1), so a huge file costs memory | review 1's note; read, not probed | 2026-11-13, rp3 review 1 |
| n122 | S4 | `gather.py` `bound` | assumes `map_free`'s `fn` gives text: a None in a row's name, detail or a line raises in `_cut`, and a lone surrogate raises `UnicodeEncodeError`; the join's contract | review 1's note; read, not run | 2026-11-13, rp3 review 1 |
| n123 | S4 | `gather.py` `facts` | catches `Exception` from `read_doctor`, so a `SystemExit` raised by an in-process doctor passes through; the join's concern | review 1's note; read | 2026-11-13, rp3 review 1 |
| n124 | S4 | `gather.py` `system` | a release of dots alone (`...`) is kept as it is; only one with no leading digit or dot reads `unreadable`; cosmetic | review 1's note; read | 2026-11-13, rp3 review 1 |
| n125 | S4 | `gather.py` version patterns | `VERSION` and `CLAUDE` admit up to 36 freely chosen digits (`[0-9]{1,9}` three times and an rc number), a side channel in theory only | review 1's note; read | 2026-11-13, rp3 review 1 |
| n126 | S4 | commits | each commit's author line carries the account's git identity; the repo's practice, not one slice's | review 1's note | 2026-11-13, rp3 review 1 |
| n127 | S4 | `plugins/suite` `form.py` `nothing_new` | the known words come from `build`'s bytes, where a cell's pipe is written escaped, so a render quoting a check's detail that holds a pipe misses on a word the draft holds and falls back to the template; read the escape back first | review 1's R1-F4, probe p5 | 2026-11-13, rp4 review 1 |
| n128 | S4 | `plugins/suite` `form.py` | GitHub's own drawing of the form is not verified: pandoc's GFM stands in; a placeholder inside a code span, a title's `#12` or backticks on GitHub are the look the row owes | review 1's note 1, probe p2 | 2026-11-13, rp4 review 1 |
| n129 | S4 | `plugins/suite` `form.py` | a bidi control (U+202E) in a value is accepted and drawn inside `<code>`, its reordering of the labels after it in a browser unverified; NUL, ESC and other C0 controls read back, NUL drawn as U+FFFD; their removal is rp2's and rp5's | review 1's note 2 | 2026-11-13, rp4 review 1 |

## From packet rp4-form (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n130 | S4 | `plugins/suite` `form.py` `title` | the title is cut on a code point, not a grapheme: a flag pair is split, a ZWJ sequence left ending in ZWJ, a combining accent dropped from its letter; R5's character edge is met | review 1's note 3, probe p7 | 2026-11-13, rp4 review 1 |
| n131 | S4 | `plugins/suite` `form.py` `title` | the verb is compared case-sensitively: `title("doctor", "Doctor: failing")` gives `doctor: Doctor: failing` | review 1's note 4 | 2026-11-13, rp4 review 1 |
| n132 | S4 | `plugins/suite` `form.py` `subject` | digits leave a check's name too, so `py39` and `py312` give one fingerprint (design item 11); no command and no row of the tool gives `check:<tool>::`; a `ran` of spaces gets a check subject while the form writes `(empty)` | review 1's note 5, probe p4 | 2026-11-13, rp4 review 1 |
| n133 | S4 | `plugins/suite` `form.py` `nothing_new` | by the rule's letter a new sentence's opener (`The`, `It`) misses unless the form holds the word, `e.g.` misses, a possessive of a hyphened word misses; a lowercase name, a ZWJ-joined one or a backslash path passes and `added` lists it | review 1's note 6, probe p5 | 2026-11-13, rp4 review 1 |
| n134 | S4 | `plugins/suite` `form.py` `fit` | a fit that drops every row (all `warn`) leaves an empty table under a summary that still counts them; a form of exactly 4,096 bytes stays, as `send`'s ceiling reads it | review 1's note 7, probe p6 | 2026-11-13, rp4 review 1 |
| n135 | S4 | `plugins/suite` `form.py` `draft` | a plugin's version is not normalised: `1.2` gives fields that `build` refuses (`field plugins`); gather does not say it normalises plugin versions, so the join should check | review 1's note 8 | 2026-11-13, rp4 review 1 |
| n136 | S4 | `plugins/suite` `form.py` `parse` | every name of the Versions line, the Plugins line and the rows is checked against `tools`, so `send` passes the public tools with `suite` and `door`; the first build's decide line | review 1's note 9 | 2026-11-13, rp4 review 1 |
| n137 | S4 | `plugins/suite` `form.py` `put` | `put` takes `rows.01.name` as row 1, a key `free` never lists | review 1's note 10 | 2026-11-13, rp4 review 1 |

## From packet rp2 (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n138 | S4 | `scripts/hygiene` `lan`, `email` | quadratic on a long dashed run with a `.`: 0.55 s at 10 KB, 13.1 s at 40 KB; nearly every text holds a `.`, so the scrub's gate rarely skips `lan` | review 1's notes; 0.60 s at 10 KB on the fix | 2026-11-13, rp2 review 1 |

## From packet rp2-scrub (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n139 | S4 | `plugins/suite` `scrub.py` `_reach` | counts quotes from the line's start for each path: one line of 10,000 paths takes 9.3 s, 66,000 paths on their own lines 1.9 s | review 1's notes | 2026-11-13, rp2 review 1 |
| n140 | S4 | `plugins/suite` `scrub.py` `_assign` | a password glued to its flag (`-p<value>`, as mysql takes it) is no flag, so its value stays | review 1's T3 | 2026-11-13, rp2 review 1 |
| n141 | S4 | `plugins/suite` `scrub.py` `_emails` | an email whose domain runs on into more text holding a digit keeps its local part; found only in a fuzz of glued pieces | review 1's notes, its fuzz | 2026-11-13, rp2 review 1 |
| n142 | S4 | `plugins/suite` `scrub.py` `strike` | `strike` and `spans` assume a text with no plane-15 private-use character: `scrub` cleans first, but `strike` on a hand-edited draft holding one indexes past its seals | review 1's notes, not run | 2026-11-13, rp2 review 1 |
| n143 | S4 | rp4 the form | GitHub renders an unfenced `<path-1>` as an unknown HTML tag, so a placeholder may vanish on the page | review 1's notes, not verified | 2026-11-13, rp2 review 1 |

## From packet rp2-scrub (review 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n144 | S4 | `plugins/suite` `scrub.py` `MAC` | six parts of one or two hex digits joined by colons are a MAC now: `a:b:c:d:e:f flags` and `ratio 1:2:3:4:5:6` give `<address-1>` | review 2's own10 M10 | 2026-11-13, rp2 review 2 |
| n145 | S4 | `plugins/suite` `scrub.py` `MAC` | a dotted date or build number of three groups of four hex digits, `build 2024.1113.1230`, is the dotted MAC and gives `<address-1>` | review 2's own10 M11 | 2026-11-13, rp2 review 2 |
| n146 | S4 | `plugins/suite` `scrub.py` `_emails` | the walk back to a colon takes prose and half a time: `12:30:45 INFO mail sent to <x>` gives `12:30:<name-1> <email-1>` | review 2's own10 N4, N5 | 2026-11-13, rp2 review 2 |
| n147 | S4 | `plugins/suite` `scrub.py` `_auth` | a plain word after an `authorization:` name is taken: `authorization: denied` gives `authorization: <secret>`, and the rest of the line goes with it | review 2's own10 Z4 | 2026-11-13, rp2 review 2 |

## From packet rp5-send (review 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n148 | S4 | `tests/test_rp5_send.py` `DoorTest` | the line-11 walk matches a starter by its name and reads `str` constants alone, so a second create through an alias (`_P = subprocess.Popen`) or a bytes argv passes; flag a name bound to a starter, read `bytes` as words | review 2's R2-F3, two mutants `OK` | 2026-11-13, rp5 review 2 |
| n149 | S4 | `plugins/suite` `send.py` `BLANK` | outside item 4(e)'s list, these pass `check` and the screen and are filed: U+16FE4, U+1D159, U+FFFC, a combining flood, U+0488, a lone U+1F3FB, trailing spaces; a run of U+16FE4 could carry a count unseen | review 2's notes, `probes/p1.py` | 2026-11-13, rp5 review 2 |
| n150 | S4 | `plugins/suite` `send.py` `unseen` | the `nfkc` kind refuses every line NFKC changes, `…`, `™`, `µ` and `½` among them; if the form puts one in a fixed line or a title, every draft is refused. Measured at phase 2: the form's fixed lines hold none, and a clean draft of each public tool checks clean | review 2's notes | 2026-11-13, rp5 review 2 |
| n151 | S4 | `plugins/suite` `send.py` `_issue` | an approval can still be made by a direct call in the same process, `send._issue(data, repo, login)`, with no screen; Python has no private names | review 2's notes | 2026-11-13, rp5 review 2 |

## From packet sc4-errors (build 1 and review 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n152 | S4 | `plugins/suite` `term.py` `error` | a typed word in a cause is cleaned of control bytes but not quoted, so `agentik 'a b'` reads `a b is not a verb or a tool`; the `next:` line is quoted by `shlex` | read, not run | 2026-11-13, sc4 build 1 |
| n153 | S4 | `plugins/suite` `cli.py` `_bad_flag` | a value flag typed with no value (`status --ps`) reads `--ps is not a flag of status`, which is false; a cause of its own, `--ps needs a value`, would say it | read in `_parse`, not run | 2026-11-13, sc4 build 1 |
| n155 | S4 | `plugins/suite` `term.py` `_ordered` | U+061C, U+200E, U+200F and the Cf characters (U+200B, U+2060, U+FEFF, U+00AD, U+180E, U+206A) reach the cause and `next:` lines; settled where this row's `_ordered` and su2-screen's `clean` meet | review 2's F3 | 2026-11-13, sc4 review 2 |
| n156 | S4 | `plugins/suite` `cli.py` `do_version` | with no manifest, `version`'s `next:` is `claude plugin install suite@agentik`, the suite's one remedy that starts `claude` and installs; sc11 may weigh it against `agentik setup suite` | review 2's F5, a copy with `plugin.json` removed | 2026-11-13, sc4 review 2 |

## From packets su2-read and su2-screen (review 1 and phase 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n157 | S4 | `plugins/suite` `status_read.py` `_sessions` | a seat id not shaped 8-4-4-4-12 hex is never matched to its process, and its row counts as bare; match seat ids against every later word | seats `seat-a`, `seat-b`, a row `claude --resume seat-a`: both `pid` null | 2026-11-13, su2-read review 1's R1-F5 |
| n158 | S4 | `plugins/suite` `status_read.py` `_settle` | a `schema` past 4,300 digits raises ValueError from `int()` under Python 3.11+; compare the digits' length | `x/` and 5,000 nines: ValueError under 3.14 | 2026-11-13, su2-read review 1's R1-F7 |
| n160 | S4 | `plugins/suite` `status_screen.py` `capped`, `wall` | past five sessions with no `sessions` source the cap row reads `and 5 more: ?`, no command; `%g` prints a wall of 1234567 as `1.23457e+06 s` | `capped` and `wall` | 2026-11-13, su2-screen review 1's R1-F8 |
| n161 | S4 | `plugins/suite` `status_read.py` `_remedy`, `status_screen.py` `command` | a tool's command is printed `agentik TOOL ...` where no door reaches the suite too, so pasted it is not found; sc4's `_tool_line` gives the tool's file there | read, not run | 2026-11-14, su2-read phase 2 |

## From packet rp6-verb (review 1 and build 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n162 | S4 | `plugins/suite` `issue.py` `_read`, `_new`, `_send` | the drafts path is printed raw: `new --json`'s and the bare read's `path`, and `--web`'s `The draft:` line, so `XDG_STATE_HOME`, and under the real home the login, reach stdout; print `plan.shown` or the id alone, and let the skill take the id | review 1's F7, probe D | 2026-11-14, rp6-verb review 1 |
| n163 | S4 | `plugins/suite` `scrub.py` (a) | a login inside a longer word is left in the draft, though design/22 §8 item 2 names the case; whole-word matching spares a plain-word login inside a common word, so which rule holds is the coordinator's call | review 1's F9, a lead against rp2's rule | 2026-11-14, rp6-verb review 1 |
| n164 | S4 | `plugins/suite` `scrub.py` (b) | `</details>` in the person's words is scrubbed as a one-segment path and drawn `<<path-1>>`; nothing leaks or goes live, an over-scrub of rp2's one-segment rule | review 1's F10 | 2026-11-14, rp6-verb review 1 |
| n165 | S4 | `tests/test_rp6_issue.py` | three files are opened and never closed (lines 213, 288, 348), a ResourceWarning each under `-W` | review 1's observations | 2026-11-14, rp6-verb review 1 |
| n167 | S4 | `plugins/suite` `gather.py` `_past_edge` | a one-line window over 64 KiB drops its first 1,024 bytes and the word there; a secret with spaces in it longer than that, straddling the window's start, would keep its tail | read in build 2 | 2026-11-14, rp6-verb build 2 |

## From packet in4-inbox (review 1 and phase 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n168 | S4 | `plugins/suite` `tools.py` `run_all` | a read runs in the person's cwd, so a tool that writes to its cwd writes in a checkout: `run_all` starts each job with no `cwd`, and `status` shares it; give the reads a neutral cwd | in4 review 1 F6: from cwd `T/pear-hq` a stub's `./WRITTEN-BY-TOOL` lands in the checkout | 2026-11-14, in4-inbox review 1 |
| n169 | S4 | `plugins/suite` `tools.py` `run_all` | SIGTERM or SIGHUP leaves a hung read running past the wall: `run_all` cleans up on BaseException alone; `status` shares it, and with in4's fix `status` and `inbox` map both signals to `status.Signalled`, `config` and `doctor` not | in4 review 1 F7: exit -15, the stub at ppid 1 | 2026-11-14, in4-inbox review 1 |
| n170 | S4 | `plugins/suite` `inbox.py` `_reads` | the wall is not the whole run's: `describe_all`'s own 2 s, then the reads' 5 s, so a hung describe-only tool beside three hung reads takes 7.06 s while each row says `gave no answer in 5 s` | in4 review 1 F9, `agentik-slow` beside three sleeping reads | 2026-11-14, in4-inbox review 1 |
| n171 | S4 | `tests/test_agentik_suite.py` `WallTest.test_f4_a_child_that_left_the_group_and_holds_stdout` | the test's 3.0 s bound is missed on a loaded machine: 3.19 s while three other gate jobs ran, 711 of 712 passed, and the same head was green in the job before; widen the bound or measure against an idle baseline | a landing's `make check` | 2026-11-14, in4-inbox phase 2 |

## From the Open table (n172 to n175, moved by up3-forward-only's phase 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n172 | S4 | `plugins/suite` the refresh at SessionStart | the refresh at SessionStart moves only a launcher whose tree its own plugin froze: not held by fk2-plan, so an enabled copy numerically newer can still replace a fork's launcher | hq design/25 §3 item 16, R1-F2 | 2026-11-14, fk2-plan build 1 |
| n173 | S4 | `bin/agentik` | a folder whose path holds a space is printed as `that folder` in the list the door shows when no suite is installed: safe, and the path is lost | sc13 review 2 N1 | 2026-11-14, sc13-door review 2 |
| n174 | S4 | `form.nothing_new` | a render that inverts or empties Expected using only words the draft holds is saved as it stands, and no word is marked unsure; that check is reword's road, so it is not rp8's | rp8 review 1 F6 | 2026-11-14, rp8-respeak review 1 |
| n175 | S4 | `render.run` | a signal that arrives in the last instructions of `run`, after the last check and before the old handlers are back, is recorded and never raised; one that arrives inside `mkdtemp` leaves an empty folder; read in the code, not reproduced | rp8 review 2 N2 | 2026-11-14, rp8-respeak review 2 |

## From the Open table (n176 to n179, moved by dr1-door-ahead's phase 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n176 | S4 | the suite's start | Ctrl-C while a verb's imports load, its first 100 ms or so, prints a `KeyboardInterrupt` traceback and exits by the signal, for `config` and `issue new` alike, and on main too | rp8 review 2 N3 | 2026-11-14, rp8-respeak review 2 |
| n177 | S4 | `plugins/suite` `config.py` `_tool` | `config suite` words each config-read warning but `choice` as `unknown key`, so a `sources` line the suite passes over reads `unknown key sources.suite`; the doctor's `doctor.settings.*` words could serve | `config.py:403`, a user file naming `suite` under `sources:` | 2026-11-14, fk2b-reads build 1 |
| n178 | S4 | `doctor` | a group line can carry the mark FAIL beside a warn's words: where a tool's own doctor fails in a home with a source warn, the line reads `FAIL  murmur  2 plugins of this name are installed, and no source is declared`; the exit (1) and the close are right | hI with a failing launcher doctor (review 1's `p10_fail.py`) | 2026-11-14, fk2b-reads review 1's leads |
| n179 | S4 | `tests/test_agentik_suite.py` `WallTest.test_f2_twenty_slow_tools_add_nothing_past_the_wall` | n171's 3.0 s bound in a second test: `config` took 3.02 s at load 8 beside another check, and was green alone three times at the same head; one bound for both tests, widened or measured against an idle baseline | gate 20261114-061401-1894 | 2026-11-14, fh13-relay-plan build 1 |

## From the Open table (n180 and n182, moved by ic2-needs' phase 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n180 | S4 | `plugins/suite` `plan.py` step 3, `cli.py` `_not_a_verb` | a tool with a `page` and a held or unfound source: setup's plan shows step 3's lone row, no step 4 or 7 row and never the page, while `T doctor` refuses with the page | review 1 lead, homes hB, hH, pC | 2026-11-14, fh13-relay-plan fix of review 1 |
| n182 | S4 | `plugins/suite` `cli.py` `help_verb` | the sentence under `usage:` in `help <verb>` is not wrapped to the width, so the terminal breaks it mid-word: `help doctor` at 60 columns has a line of 103 characters | sc5 review 1 N1 | 2026-11-14, sc5-first-screen review 1 |

## From packet ak4a-update (n183 and n184, moved by ic2-needs' phase 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n183 | S4 | `plugins/suite` `update.py` | where the suite was placed from a checkout, `update` cannot name that checkout, since `install-cli` records the tree's hash and version but not the folder it froze from; recorded, the note could name the folder | `agentik_install.read_launcher` reads VERSION, TREE, PYTHON | 2026-11-14, ak4a build 1 |
| n184 | S4 | `plugins/suite` `update.py` `main`, `cli.py` `err.setup.name` | `update zzz`, a well-formed name that is no plugin of the list, gets setup's refusal for a bad name (`zzz is not a plugin name: lowercase letters, digits and dashes`), whose words say its shape is wrong; words for a name the list does not hold | review 1 lead | 2026-11-14, ak4a review 1 |

## From packet ak4a-update (n185, moved by ic2-needs' phase 2 for review 2's lead)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n185 | S4 | `plugins/suite` `plan.py` `_command` | an `installPath` that links out of the plugins folder to a checkout gets that checkout's `bin/agentik-T install-cli` run by `update` and `setup` alike, since `_command` checks under the root, not under the plugins folder; setup's rule | review 1 probe f | 2026-11-14, ak4a review 1 |

## From the Open table (n199, n198, n196 and n195, moved by ak10c1-read-wall)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n199 | S4 | `plugins/suite` `doctor.py` `close_command` | where a failing group of R5's comes first, R7's plain close takes the close from a later group on sc10's path, and that group's row gains its `fix:` line; first match by design | review 2's lead, `probe_mix.py` s1 | 2026-11-14, ak9b-plug-reader review 2 |
| n198 | S4 | `plugins/suite` `doctor.py` `doctor_read` | an R5 doctor read whose `argv` is `[""]`, or opens with a flag (`["--json"]`), still counts and runs the tool with no verb, so its row reads unreadable; only an empty `argv` was ruled | review 2's lead | 2026-11-14, ak9b-plug-reader review 2 |
| n196 | S4 | `plugins/suite` `doctor.py` | R3's reason shows on the config screens only: `doctor` prints `ok  T  its doctor passed` for a tool whose describe answers under another tool's name, with no reason beside it | review 1 lead, R8's "with R3's reason where it applies"; build 1 left it not done | 2026-11-14, ak9b-plug-reader review 1 |
| n195 | S4 | `plugins/suite` `config.py` `--json` | `config --json` carries a describe's `summary` whole, so a 200 KB summary is 200 KB of the answer, as at the pin; R4's 300-character cut reaches the error's message only | review 1 lead, a 200 KB summary | 2026-11-14, ak9b-plug-reader review 1 |

## From packet ak4a-update (n186 to n190, moved by ak12-polish)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n186 | S4 | `plugins/suite` `update.py` `runner_pid` | the hold tries every prefix of a process line as the program, so a `make` or a `git -C` in the runner's checkout whose later word is `run`, `gate` or `plan` holds an update; narrow the walk to a prefix that is an executable file | review 2 lead, probe 2A test_a3 | 2026-11-14, ak4a review 2 |
| n187 | S4 | `plugins/suite` `update.py` `do_update` | after a plugin update drops a tool's entry, the next `update` reads the tool as absent and says everything is current, with nothing about the tool that was lost | review 2 lead, F4 rerun without mending | 2026-11-14, ak4a review 2 |
| n188 | S4 | `plugins/suite` `update.py` `--json` | `update NAME --json` for a listed tool that is not installed prints an object that does not name it: `tools` and `skipped` are both `[]` | review 2 lead | 2026-11-14, ak4a review 2 |
| n189 | S4 | `plugins/suite` `update.py` `update.skip.id` | the skip row for an id that is no plugin id gives no next step | review 2 lead | 2026-11-14, ak4a review 2 |
| n190 | S4 | `plugins/suite` `update.py` `err.update.left` | a run that leaves a step 3 row to do prints an ok row for the same tool above it, and that row's words are setup's (`setup would install it again`) | review 2 lead, F5's run | 2026-11-14, ak4a review 2 |

## From packets ak9b-plug-reader and ak9c-plug-rest (n191 to n194, n200 to n202, moved by rr7-way-in)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n191 | S4 | `plugins/suite` `update.py` | with output sent to a file, `agentik update` prints its `running claude plugin marketplace update agentik` line above the plan's first line, since the two streams are not flushed in order; not fixed | the first real run of `agentik update`, in ak9b-plug-reader's start line | 2026-11-14, ak9b-plug-reader build 1 |
| n192 | S4 | `plugins/suite` `config.py` `_list` | in `agentik config`, R3's reason is a cell after the state, in the settings column, so where one reason shows every row's `N settings` pads by about 27 columns | review 1 lead, the config table at the pin and at head | 2026-11-14, ak9b-plug-reader review 1 |
| n193 | S4 | `tests/test_sc10_doctor_checks.py` a10, `tests/test_ak3d_doctor.py` line 5 | the two timing tests set `tools.WALL` to 0.5 s, so no test holds the describe wall R5 adds before the doctor's deadline at its real 2 s (a worst case of 32 s, against 30 s at the pin) | review 1 lead, six hung tools: 5.0 s at head, 3.0 s at the pin, the deadline at 3 | 2026-11-14, ak9b-plug-reader review 1 |
| n194 | S4 | `plugins/suite` `cli.py` `help` | where a plugin's command sits under its root off PATH (fk_homes hD), `agentik help T` exits 3 while `agentik T --help` runs the tool's file (R1) | review 1 lead, the exit code alone seen | 2026-11-14, ak9b-plug-reader review 1 |
| n200 | S4 | `plugins/suite` `cli.py` help | `help` lists no claimed verb: a word a tool claims runs from `agentik <word>`, and no help screen names it | brief R9; design/15 P2 | 2026-11-14, ak9c build 1 |
| n201 | S4 | `plugins/suite` `tools.py` `claims` | a claim of a word that is a tool's or a plugin's name reads as counting in `config T --json`, though `_not_a_verb` settles that word first and never runs the claim | read; `cli.py` `_not_a_verb` | 2026-11-14, ak9c build 1 |
| n202 | S4 | `plugins/suite` `tools.py` `describe_all` | a describe that hangs is never cached, so a word that is nothing pays the whole wall each time while a tool hangs: 2.06 s against the pin's 0.05 s with six hanging tools; inside R6's wall | review 1's lead, probe `cost` | 2026-11-14, ak9c review 1 |

## From the Open table (n203, n205 to n208, moved by rc0-records-cut)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n203 | S4 | `config.py` | an `unknown` or `choice` warning with a null `line` prints `<path>:None` | config.py:474 | 2026-11-14, ak9d |
| n205 | S4 | `agentik_install.py` `_lock` | the share swapped for a link between the plan and the lock: every row is kept, yet `.lock` is made in the link's target, as `O_NOFOLLOW` guards the last component alone. Fix if wanted: open the share `O_NOFOLLOW`, match the plan's inode, open `.lock` by `dir_fd` | review 2's lead, `race-share-to-link` | 2026-11-14, ak4b-uninstall review 2 |
| n206 | S4 | `agentik_install.py` `_lock` | the re-check loop (`while True`) has no bound: it spins while something replaces `.lock` on every turn, which neither install-cli nor uninstall does | review 2's lead; read, not reproduced | 2026-11-14, ak4b-uninstall review 2 |
| n207 | S4 | `agentik_install.py` `_plan` | one share under two prefixes: where `<prefix>/share` links to another prefix's share, uninstall removes that prefix's trees and share and leaves its launcher naming a gone tree; as at 93e3eb0 | review 2's lead, `share-parent-link-to-A-share` | 2026-11-14, ak4b-uninstall review 2 |
| n208 | S4 | `agentik_install.py` `_ours` | a launcher that sets TREE by `unset`, `read` or `eval` after the template's `TREE=` line still reads as install-cli's; comparing the file with the template rendered whole would close it | ak4b-uninstall's last read | 2026-11-14 ak4-remove |

## From the Open table (n209, moved by rc0-records-cut)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n209 | S4 | `tests/test_ak4b_uninstall.py` | `_lock`'s `fstat` regular-file check is pinned by no test, and `test_a_lock_fifo_or_folder_keeps_all` raises `TimeoutError` from its alarm, an `OSError` that `uninstall` keeps, so it cannot fail on a hang | ak4b-uninstall's last read | 2026-11-14 ak4-remove |

## From packet ak11-init (build 1 and review 1) (n210, n211, n213 to n215, moved by rc0-records-cut)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n210 | S4 | `scripts/sync`, `plugins/suite/lib/scaffold/hq` | `sync` places no record check in a scaffolded hq: `init --kind hq` writes a copy of `scripts/recordlint` and its sha256 line, and nothing says how an hq takes a newer one; a later row, or a line in the scaffold's README | the scaffold's `Makefile`, target `recordlint`; `scripts/sync`'s usage | 2026-11-15, ak11-init build 1 |
| n211 | S4 | `plugins/suite` `init.py` `parent_shown`, `--dry-run` | DIR `.` in a parent init cannot write: `--dry-run` exits 0, then the write exits 1 naming `.`, not its parent; name the real parent, and have the dry run check that it can write there | ak11-init review 1, F3 | 2026-11-15, ak11-init review 1 |
| n213 | S4 | `plugins/suite` `init.py` wording | a dangling link at DIR is called a file (`not_a_folder`), and a failed rename of the whole stage names `<dir>/.` (`pear/.`); a line of its own for a link, and DIR as typed | ak11-init review 1, F6 | 2026-11-15, ak11-init review 1 |
| n214 | S4 | `plugins/suite` `status.py` rows part | `pushed` rows with owed lines lead the part: sort the rows by stage, `building` first, so the work in flight shows before the work that waits | su6-rows-part review 1 | 2026-11-15, su6-rows-part review 1 |
| n215 | S4 | `plugins/suite` `status.py` rows read | the rows read is the slowest status source and grows with the rows (3.8 s for 38 rows, under a 6 s wall); read only the rows not closed, or cache the read | su6-rows-part review 1 | 2026-11-15, su6-rows-part review 1 |

## From packet sc6-config (review 1) (n216, n217, moved by ak10c5-table-gone)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n216 | S4 | `plugins/suite` `config.py` step 1's `next:` | step 1's `next:` counts a tool with 0 keys: on a tie it names `emptytool` over `loom`; prefer a tool with `n > 0` (R2's tie rule holds) | `emptytool` (0 keys) beside `loom` (24), none changed, suite silent: `next: config emptytool`, a screen with no `next:` | 2026-11-15, sc6-config review 1 |
| n217 | S4 | `plugins/suite` `config.py` states | step 1 says `failtool  did not answer` while step 2 says `failtool answers, but the answer of its keys cannot be read.`: the two screens give one state two accounts (`config.state.read_unreadable` and its kin) | `config` then `config failtool`, a stub whose `describe config --json` exits 1 | 2026-11-15, sc6-config review 1 |

## From packet sc6-config (review 1) (n218, moved by sn1-need-notread)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n218 | S4 | `plugins/suite` `config.py` prefix form `--json` | `config loom.ink --json` prints the whole-tool object cut to the prefix's keys, with no prefix field and unfiltered warnings (`inq.weight` stays), which the text form filters; the pin refused it | `config loom.ink --json \| grep inq.weight` finds it; `config loom.ink` does not show it | 2026-11-15, sc6-config review 1 |
