# Nice to have

Findings that block nothing, one row each, in hq design/05 §2's table; `scripts/recordlint` holds it. The list before 2026-11-01 is frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet that touches an area greps them by path.

## Open

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n199 | S4 | `plugins/suite` `doctor.py` `close_command` | where a failing group of R5's comes first, R7's plain close takes the close from a later group on sc10's path, and that group's row gains its `fix:` line; first match by design | review 2's lead, `probe_mix.py` s1 | 2026-11-14, ak9b-plug-reader review 2 |
| n198 | S4 | `plugins/suite` `doctor.py` `doctor_read` | an R5 doctor read whose `argv` is `[""]`, or opens with a flag (`["--json"]`), still counts and runs the tool with no verb, so its row reads unreadable; only an empty `argv` was ruled | review 2's lead | 2026-11-14, ak9b-plug-reader review 2 |
| n197 | S3 | `config.py` `asks`, `doctor.py` `_closes` | sc5 R8's word rule, in both: a quoted `'-y'` or `"--yes"` and a cluster such as `-yq` pass it, so the remedy goes behind `next:`, the pin's doctor too; one rule for both (quotes stripped, a cluster holding `y`), ruling on `--YES`, `REMOVE`, `--assume-yes` | review 2 F1, the remedy `murmur reset -yq` | 2026-11-14, ak9b-plug-reader review 2 |
| n196 | S4 | `plugins/suite` `doctor.py` | R3's reason shows on the config screens only: `doctor` prints `ok  T  its doctor passed` for a tool whose describe answers under another tool's name, with no reason beside it | review 1 lead, R8's "with R3's reason where it applies"; build 1 left it not done | 2026-11-14, ak9b-plug-reader review 1 |
| n195 | S4 | `plugins/suite` `config.py` `--json` | `config --json` carries a describe's `summary` whole, so a 200 KB summary is 200 KB of the answer, as at the pin; R4's 300-character cut reaches the error's message only | review 1 lead, a 200 KB summary | 2026-11-14, ak9b-plug-reader review 1 |
| n194 | S4 | `plugins/suite` `cli.py` `help` | where a plugin's command sits under its root off PATH (fk_homes hD), `agentik help T` exits 3 while `agentik T --help` runs the tool's file (R1) | review 1 lead, the exit code alone seen | 2026-11-14, ak9b-plug-reader review 1 |
| n193 | S4 | `tests/test_sc10_doctor_checks.py` a10, `tests/test_ak3d_doctor.py` line 5 | the two timing tests set `tools.WALL` to 0.5 s, so no test holds the describe wall R5 adds before the doctor's deadline at its real 2 s (a worst case of 32 s, against 30 s at the pin) | review 1 lead, six hung tools: 5.0 s at head, 3.0 s at the pin, the deadline at 3 | 2026-11-14, ak9b-plug-reader review 1 |
| n192 | S4 | `plugins/suite` `config.py` `_list` | in `agentik config`, R3's reason is a cell after the state, in the settings column, so where one reason shows every row's `N settings` pads by about 27 columns | review 1 lead, the config table at the pin and at head | 2026-11-14, ak9b-plug-reader review 1 |
| n191 | S4 | `plugins/suite` `update.py` | with output sent to a file, `agentik update` prints its `running claude plugin marketplace update agentik` line above the plan's first line, since the two streams are not flushed in order; not fixed | the first real run of `agentik update`, in ak9b-plug-reader's start line | 2026-11-14, ak9b-plug-reader build 1 |
| n182 | S4 | `plugins/suite` `cli.py` `help_verb` | the sentence under `usage:` in `help <verb>` is not wrapped to the width, so the terminal breaks it mid-word: `help doctor` at 60 columns has a line of 103 characters | sc5 review 1 N1 | 2026-11-14, sc5-first-screen review 1 |
| n180 | S4 | `plugins/suite` `plan.py` step 3, `cli.py` `_not_a_verb` | a tool with a `page` and a held or unfound source: setup's plan shows step 3's lone row, no step 4 or 7 row and never the page, while `T doctor` refuses with the page | review 1 lead, homes hB, hH, pC | 2026-11-14, fh13-relay-plan fix of review 1 |
| n176 | S4 | the suite's start | Ctrl-C while a verb's imports load, its first 100 ms or so, prints a `KeyboardInterrupt` traceback and exits by the signal, for `config` and `issue new` alike, and on main too | rp8 review 2 N3 | 2026-11-14, rp8-respeak review 2 |
| n179 | S4 | `tests/test_agentik_suite.py` `WallTest.test_f2_twenty_slow_tools_add_nothing_past_the_wall` | n171's 3.0 s bound in a second test: `config` took 3.02 s at load 8 beside another check, and was green alone three times at the same head; one bound for both tests, widened or measured against an idle baseline | gate 20261114-061401-1894 | 2026-11-14, fh13-relay-plan build 1 |
| n203 | S4 | `config.py` | an `unknown` or `choice` warning with a null `line` prints `<path>:None` | config.py:474 | 2026-11-14, ak9d |
| n204 | S3 | `status_read.py` the draw | `status` asks only the tools whose `agentik-<tool>` is on PATH, so a tool installed as a plugin alone is read by `config` and `doctor` and never by `status`; `inbox` asks PATH alone too, and runs PATH's file with no pass of the finder | status_read.py:357, inbox.py:91; review 1 F1's repro | 2026-11-14, ak9d review 1 |
| n205 | S4 | `agentik_install.py` `_lock` | the share swapped for a link between the plan and the lock: every row is kept, yet `.lock` is made in the link's target, as `O_NOFOLLOW` guards the last component alone. Fix if wanted: open the share `O_NOFOLLOW`, match the plan's inode, open `.lock` by `dir_fd` | review 2's lead, `race-share-to-link` | 2026-11-14, ak4b-uninstall review 2 |
| n206 | S4 | `agentik_install.py` `_lock` | the re-check loop (`while True`) has no bound: it spins while something replaces `.lock` on every turn, which neither install-cli nor uninstall does | review 2's lead; read, not reproduced | 2026-11-14, ak4b-uninstall review 2 |
| n207 | S4 | `agentik_install.py` `_plan` | one share under two prefixes: where `<prefix>/share` links to another prefix's share, uninstall removes that prefix's trees and share and leaves its launcher naming a gone tree; as at 93e3eb0 | review 2's lead, `share-parent-link-to-A-share` | 2026-11-14, ak4b-uninstall review 2 |
| n208 | S4 | `agentik_install.py` `_ours` | a launcher that sets TREE by `unset`, `read` or `eval` after the template's `TREE=` line still reads as install-cli's; comparing the file with the template rendered whole would close it | ak4b-uninstall's last read | 2026-11-14 ak4-remove |
| n209 | S4 | `tests/test_ak4b_uninstall.py` | `_lock`'s `fstat` regular-file check is pinned by no test, and `test_a_lock_fifo_or_folder_keeps_all` raises `TimeoutError` from its alarm, an `OSError` that `uninstall` keeps, so it cannot fail on a hang | ak4b-uninstall's last read | 2026-11-14 ak4-remove |

## From packet ak3p (the join of ak2b-reach, ak3-setup and ak3d-doctor)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n76 | S3 | `plugins/suite` `settings.py` `read` | a FIFO at the user settings file hangs `doctor` and `status --check` with no deadline: the read opens it; refuse a file that is not regular, as `read_regular` does for the plan's reads | ak3d review 1's R1-F1: doctor past 15 s; the same read ak2b fix round 1 left alone | 2026-11-13, ak3d review 1 |

## From packet sc4-errors (build 1 and review 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n154 | S3 | `plugins/suite` `cli.py` `_takes` | a mended `config` line is still refused for a second wrong word: `confg x` gives `config x`, which pasted reads `x is not a tool here`, exit 2 (55 lines of the sweep); `offer` could check the first name against the tools and plugins | review 2's F2 | 2026-11-13, sc4 review 2 |

## From packet fk2b-reads (build 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n177 | S4 | `plugins/suite` `config.py` `_tool` | `config suite` words each config-read warning but `choice` as `unknown key`, so a `sources` line the suite passes over reads `unknown key sources.suite`; the doctor's `doctor.settings.*` words could serve | `config.py:403`, a user file naming `suite` under `sources:` | 2026-11-14, fk2b-reads build 1 |
| n178 | S4 | `doctor` | a group line can carry the mark FAIL beside a warn's words: where a tool's own doctor fails in a home with a source warn, the line reads `FAIL  murmur  2 plugins of this name are installed, and no source is declared`; the exit (1) and the close are right | hI with a failing launcher doctor (review 1's `p10_fail.py`) | 2026-11-14, fk2b-reads review 1's leads |

## From packet ak4a-update (build 1, reviews 1 and 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n183 | S4 | `plugins/suite` `update.py` | where the suite was placed from a checkout, `update` cannot name that checkout, since `install-cli` records the tree's hash and version but not the folder it froze from; recorded, the note could name the folder | `agentik_install.read_launcher` reads VERSION, TREE, PYTHON | 2026-11-14, ak4a build 1 |
| n184 | S4 | `plugins/suite` `update.py` `main`, `cli.py` `err.setup.name` | `update zzz`, a well-formed name that is no plugin of the list, gets setup's refusal for a bad name (`zzz is not a plugin name: lowercase letters, digits and dashes`), whose words say its shape is wrong; words for a name the list does not hold | review 1 lead | 2026-11-14, ak4a review 1 |
| n185 | S4 | `plugins/suite` `plan.py` `_command` | an `installPath` that links out of the plugins folder to a checkout gets that checkout's `bin/agentik-T install-cli` run by `update` and `setup` alike, since `_command` checks under the root, not under the plugins folder; setup's rule | review 1 probe f | 2026-11-14, ak4a review 1 |
| n186 | S4 | `plugins/suite` `update.py` `runner_pid` | the hold tries every prefix of a process line as the program, so a `make` or a `git -C` in the runner's checkout whose later word is `run`, `gate` or `plan` holds an update; narrow the walk to a prefix that is an executable file | review 2 lead, probe 2A test_a3 | 2026-11-14, ak4a review 2 |
| n187 | S4 | `plugins/suite` `update.py` `do_update` | after a plugin update drops a tool's entry, the next `update` reads the tool as absent and says everything is current, with nothing about the tool that was lost | review 2 lead, F4 rerun without mending | 2026-11-14, ak4a review 2 |
| n188 | S4 | `plugins/suite` `update.py` `--json` | `update NAME --json` for a listed tool that is not installed prints an object that does not name it: `tools` and `skipped` are both `[]` | review 2 lead | 2026-11-14, ak4a review 2 |
| n189 | S4 | `plugins/suite` `update.py` `update.skip.id` | the skip row for an id that is no plugin id gives no next step | review 2 lead | 2026-11-14, ak4a review 2 |
| n190 | S4 | `plugins/suite` `update.py` `err.update.left` | a run that leaves a step 3 row to do prints an ok row for the same tool above it, and that row's words are setup's (`setup would install it again`) | review 2 lead, F5's run | 2026-11-14, ak4a review 2 |

## From packet ak9c-plug-rest (build 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n200 | S4 | `plugins/suite` `cli.py` help | `help` lists no claimed verb: a word a tool claims runs from `agentik <word>`, and no help screen names it | brief R9; design/15 P2 | 2026-11-14, ak9c build 1 |
| n201 | S4 | `plugins/suite` `tools.py` `claims` | a claim of a word that is a tool's or a plugin's name reads as counting in `config T --json`, though `_not_a_verb` settles that word first and never runs the claim | read; `cli.py` `_not_a_verb` | 2026-11-14, ak9c build 1 |
| n202 | S4 | `plugins/suite` `tools.py` `describe_all` | a describe that hangs is never cached, so a word that is nothing pays the whole wall each time while a tool hangs: 2.06 s against the pin's 0.05 s with six hanging tools; inside R6's wall | review 1's lead, probe `cost` | 2026-11-14, ak9c review 1 |

## From packet ak11-init (build 1 and review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n210 | S4 | `scripts/sync`, `plugins/suite/lib/scaffold/hq` | `sync` places no record check in a scaffolded hq: `init --kind hq` writes a copy of `scripts/recordlint` and its sha256 line, and nothing says how an hq takes a newer one; a later row, or a line in the scaffold's README | the scaffold's `Makefile`, target `recordlint`; `scripts/sync`'s usage | 2026-11-15, ak11-init build 1 |
| n211 | S4 | `plugins/suite` `init.py` `parent_shown`, `--dry-run` | DIR `.` in a parent init cannot write: `--dry-run` exits 0, then the write exits 1 naming `.`, not its parent; name the real parent, and have the dry run check that it can write there | ak11-init review 1, F3 | 2026-11-15, ak11-init review 1 |
| n212 | S3 | `plugins/suite` `init.py` `_write` | a SIGTERM while `git init` runs leaves the whole stage beside DIR as `tmpXXXXXXXX` (exit 143), and a `KeyboardInterrupt` in the move leaves part of the scaffold, as the undo runs on `OSError` alone; a stage named for DIR, SIGTERM handled, an undo on `BaseException`, re-raised | ak11-init review 1, F4 | 2026-11-15, ak11-init review 1 |
| n213 | S4 | `plugins/suite` `init.py` wording | a dangling link at DIR is called a file (`not_a_folder`), and a failed rename of the whole stage names `<dir>/.` (`pear/.`); a line of its own for a link, and DIR as typed | ak11-init review 1, F6 | 2026-11-15, ak11-init review 1 |
| n214 | S4 | `plugins/suite` `status.py` rows part | `pushed` rows with owed lines lead the part: sort the rows by stage, `building` first, so the work in flight shows before the work that waits | su6-rows-part review 1 | 2026-11-15, su6-rows-part review 1 |
| n215 | S4 | `plugins/suite` `status.py` rows read | the rows read is the slowest status source and grows with the rows (3.8 s for 38 rows, under a 6 s wall); read only the rows not closed, or cache the read | su6-rows-part review 1 | 2026-11-15, su6-rows-part review 1 |

## From packet sc6-config (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n216 | S4 | `plugins/suite` `config.py` step 1's `next:` | step 1's `next:` counts a tool with 0 keys: on a tie it names `emptytool` over `loom`; prefer a tool with `n > 0` (R2's tie rule holds) | `emptytool` (0 keys) beside `loom` (24), none changed, suite silent: `next: config emptytool`, a screen with no `next:` | 2026-11-15, sc6-config review 1 |
| n217 | S4 | `plugins/suite` `config.py` states | step 1 says `failtool  did not answer` while step 2 says `failtool answers, but the answer of its keys cannot be read.`: the two screens give one state two accounts (`config.state.read_unreadable` and its kin) | `config` then `config failtool`, a stub whose `describe config --json` exits 1 | 2026-11-15, sc6-config review 1 |
| n218 | S4 | `plugins/suite` `config.py` prefix form `--json` | `config loom.ink --json` prints the whole-tool object cut to the prefix's keys, with no prefix field and unfiltered warnings (`inq.weight` stays), which the text form filters; the pin refused it | `config loom.ink --json \| grep inq.weight` finds it; `config loom.ink` does not show it | 2026-11-15, sc6-config review 1 |
| n219 | S4 | `plugins/suite` `settings.read`, R5's line | one duplicate key makes `settings.read` fault, so every key of that file shows the bare path; a child of a flow mapping (`ink: {weight: bold}`) shows the path alone too; both within R5's letter | a file with `mode` set twice: `mode`, `ink.weight` and `page.width` all print the path with no `:line` | 2026-11-15, sc6-config review 1 |
| n220 | S4 | `plugins/suite` `config.py` groups | a key that is also a group's head (`ink` beside `ink.colour`) shows as `ink` in the `ink` group row, and `config loom.ink` prints that key's card, not the group flat | a loom with `ink` and `ink.colour` keys: `config loom` shows the `ink` group row; `config loom.ink` prints one card | 2026-11-15, sc6-config review 1 |
| n221 | S4 | `plugins/suite` `config.py` refusal | `config loom ink ''` is refused as `loom has no key ink.` with `next: config loom.ink.dry`; now that `loom.ink` is a prefix, `next: config loom.ink` is the better hint | `agentik-suite config loom ink ''` prints the refusal and the `.dry` next | 2026-11-15, sc6-config review 1 |
| n222 | S4 | `plugins/suite` `config.py` step 1 after-line | on an 80-column terminal the row of a suite whose user file does not read has an after-line of 103 columns (`... cannot be read at line 1: a tab; the subset indents with spaces`); not compared with the pin | a user config file that opens with a tab, `config` on a pty at 80 columns | 2026-11-15, sc6-config review 1 |
| n223 | S4 | `plugins/suite` `config.py` search | `config BETA`, where `beta` is a tool, is a search, not beta's screen (`config beta` shows it); R1 folds the match but not the tool-name check; fold the word before comparing with the tools' names | stubs `alpha` (key `beta.x`) and `beta`: `config BETA` lists `alpha.beta.x` | 2026-11-15, sc7-config-find review 1 |
| n224 | S4 | `plugins/suite` `config.py` search | a hyphenated word never matches a summary: `\w+` splits at `-` and `'`; `alpha.cap`'s summary "Sets the max-turns cap for a sitting." is not found by `config max-turns`, which lists only key `alpha.max-turns`; within R1's letter | stub `alpha` with keys `max-turns` and `cap`: one row | 2026-11-15, sc7-config-find review 1 |
| n225 | S4 | `term.py` `_wrap` | a key with a space wraps in two on a pty, so it cannot be read as one word: `alpha.$(touch` then `PWNED).tension` at 80 columns (28 columns, past a third); a pipe prints it whole; term's name wrapping at the pin | stub key `$(touch PWNED).tension`, `config tension` on a pty at 80 columns | 2026-11-15, sc7-config-find review 1 |
| n226 | S4 | `term.py` `fit` | `fit` can leave a space before its mark: the cut `The turns this sitting is metered …` at 66 columns; rstrip the kept text before adding `…` | `config turns` on a pty at 66 columns with a stub `session.ceilings.turns` of that summary | 2026-11-15, sc7-config-find review 1 |
| n227 | S4 | `scripts/agentik_install.py` `prune`, `uninstall` | a removed tree's bytecode stays under `<cache>/agentik/pycache/<its real path>`, the prune's and `remove <tool>`'s alike; only `remove --all` clears it | one machine: 95 MB in 4,798 files, 44 session trees' bytecode where 5 stand | 2026-11-16, the install and upgrade review, finding 14 |

## From packet up2-suite-origin (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n228 | S4 | `plugins/suite` `update.py` `suite_close` | the close can carry two `next:` lines, the doctor's then the suite's; R2 says one | review 1's F2 reproduction | 2026-11-16, up2-suite-origin review 1 |
| n229 | S4 | `plugins/suite` `update.py` `named` | reads `$HOME/.local/bin/agentik-suite` alone: a suite under another `PREFIX` is judged by HOME's launcher | review 1's lead | 2026-11-16, up2-suite-origin review 1 |
| n230 | S4 | `plugins/suite` `update.py` `suite_close` | the pull line prints with no condition: a person who just ran the README's upgrade line is told to pull again | review 1's lead | 2026-11-16, up2-suite-origin review 1 |

## From packet ic1-close (build 1, reviews 1 and 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n231 | S4 | `plugins/suite` `messages.md` `issue.strike.none` | `Struck {words} in {places}; the draft is unchanged.` says struck and unchanged at once | `issue strike` of a word the draft does not hold | 2026-11-16, ic1-close |
| n232 | S4 | `plugins/suite` `messages.md` `usage.issue` | the usage drops the `[TOOL]` that `issue new` takes (`issue.py`'s docstring: `new [TOOL]`) | `help issue`'s first line | 2026-11-16, ic1-close |
| n233 | S3 | `plugins/suite` `apply.py` `_before` | with `setup \| tee` the question can print above the plan: the flush feeds the pipe and the question reaches stderr before tee copies the plan; R4's `tee` clause was withdrawn; main prints the same | `script -q o.txt /bin/bash -c './setup \| tee /dev/null'` fed `n`: the question above the plan in 4 of 5 runs | 2026-11-16, ic1-close review 1 F1 |
| n234 | S4 | `plugins/suite` `apply.py` `show` | `update`'s and `remove`'s plans now show `get it:` under a missing `claude`, since they print through `show`; no brief named it, and it reads as a gain: confirm it or keep it to setup | `agentik-suite update` with PATH `/usr/bin:/bin`: main has no `get it:` line, the branch has one | 2026-11-16, ic1-close review 1 |
| n235 | S4 | `plugins/suite` `plan.py` `door_off` | any executable at `~/.local/bin/agentik` counts as the door; off PATH, both closes name the PATH line and hide its "holds no version" warn until PATH is mended (main ran that file, so no worse) | a script of your own there, that folder off PATH: `doctor` | 2026-11-16, ic1-close review 1 |
| n236 | S4 | `plugins/suite` `update.py`, `doctor.py`, `messages.md` | with an old Python the dry run's close and doctor's close still name `setup`, and `err.update.blocked` (update's `--json`) still says "install it"; out of reach on a Mac whose system Python is at the minimum | build 2's not-done list; read, not run | 2026-11-16, ic1-close review 2 |

## From packet rm1-leave-clean (reviews 1 and 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n237 | S4 | `bin/agentik` `back` | the door looks for a clone in the cwd alone: from a subfolder of a clone, or from `~` with the clone elsewhere, it prints the clone line, which runs but makes a second clone | `agentik nosuch` with no suite, run in `agentik-commons/docs` | 2026-11-16, rm1-leave-clean review 1 |
| n238 | S4 | `plugins/suite` `remove.py` the suite's cache row | the plan shows the suite's cache folder as kept; where `claude` takes that folder during the run, the close drops its row without a word, so plan and close differ on that row (by design) | `test_r5_the_suites_cache_gone_after_the_run_is_no_fault` | 2026-11-16, rm1-leave-clean review 1 |
| n239 | S4 | `plugins/suite` `remove.py`, GUIDE §10 | the old order's cut under a `claude` refusing an uninstall once its marketplace is gone; GUIDE's door "reads and writes nothing" yet tests the cwd; `remove` via the launcher refills the pycache it removes; `once()` keeps a folder's first spelling, so an earlier second one misses `soft` | read, not run | 2026-11-16, rm1-leave-clean review 2 |

## From packet up4-update-close (build 1, review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n240 | S4 | `plugins/suite` `apply.py` `execute`, `report` | a command that hangs is silent until its limit (600 s for `claude`, 120 s for an install-cli): no `still running` line a minute; and a run cut by `kill -9` writes no journal line, so the next run, which finishes it, no longer lists what the cut run kept | review finding 15, its other parts | 2026-11-16, up4-update-close build 1 |
| n241 | S4 | `plugins/suite` `update.py` `_run`, `main`, `page_row` | an interrupt's `next:` drops the names and `--yes`; `update NoSuch` reads `err.setup.name`; a page tool whose plugin ships its command reads `stays as it was`; `--json` has no sessions field; a long note unlaid on a pty; an interrupt in `apply.look` reads `between steps` | review 1 L2-L4, L6-L8 | 2026-11-16, up4 review 1 |

## From packet up3-forward-only (reviews 1 and 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n242 | S4 | `agentik_install.py`, `plan.py` step 4 | L1 a person's newer file reads newer to setup and doctor, yet install-cli overwrites it; L2 no test holds launcher line 2, which forward-only reads; L3, L4 a kept command: no door, PATH hint, dry-run title; L6 update reuses setup's words; L7 a `doctor.py` merge; L8 a gone `AGENTIK_PYTHON` | review 1 leads | 2026-11-16, up3 review 1 |
| n243 | S4 | each tool's `install-cli` verb, after the sync of `agentik_install.py` | no tool's verb takes `--force` yet, so after the sync each tool's install-cli says it left a newer command and names no way to place over it; the sync's row gives each verb the flag and has it call `install_cli(prefix, force=…, takes_force=True)` | review 2 L2 | 2026-11-16, up3 review 2 |
