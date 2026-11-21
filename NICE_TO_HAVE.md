# Nice to have

Findings that block nothing, one row each, in hq design/05 §2's table; `scripts/recordlint` holds it. The list before 2026-11-01 is frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet that touches an area greps them by path.

## Open

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n256 | S4 | `scripts/hygiene` `records` | a repo may extend the record names from its own `.hygiene-allow`, as a tree that keeps `.claude/` out wants | hq design/28 §11 lead 4 | 2026-11-18, rr3-records-guard |
| n204 | S3 | `status_read.py` the draw | `status` asks only the tools whose `agentik-<tool>` is on PATH, so a tool installed as a plugin alone is read by `config` and `doctor` and never by `status`; `inbox` asks PATH alone too, and runs PATH's file with no pass of the finder | status_read.py:357, inbox.py:91; review 1 F1's repro | 2026-11-14, ak9d review 1 |

## From packet ak3p (the join of ak2b-reach, ak3-setup and ak3d-doctor)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|

## From packet sc4-errors (build 1 and review 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n154 | S3 | `plugins/suite` `cli.py` `_takes` | a mended `config` line is still refused for a second wrong word: `confg x` gives `config x`, which pasted reads `x is not a tool here`, exit 2 (55 lines of the sweep); `offer` could check the first name against the tools and plugins | review 2's F2 | 2026-11-13, sc4 review 2 |

## From packet ak4a-update (build 1, reviews 1 and 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|

## From packet ak9c-plug-rest (build 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|

## From packet ak11-init (build 1 and review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n212 | S3 | `plugins/suite` `init.py` `_write` | a SIGTERM while `git init` runs leaves the whole stage beside DIR as `tmpXXXXXXXX` (exit 143), and a `KeyboardInterrupt` in the move leaves part of the scaffold, as the undo runs on `OSError` alone; a stage named for DIR, SIGTERM handled, an undo on `BaseException`, re-raised | ak11-init review 1, F4 | 2026-11-15, ak11-init review 1 |

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

## From packet dr1-door-ahead (reviews 1 and 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n244 | S4 | `update.py`, `doctor.py`, hq Makefile | leads: update `--json` on old Python says `--dry-run`, not AGENTIK_PYTHON; the doctor's old-Python row closes on a setup that refuses; no sum tool: recordlint's copy advice; sc2's `check()` skips the PATH line; a `--prefix` door gets install-cli; a close beside a second warn is setup | review 1, L1 to L6 | 2026-11-16, dr1-door-ahead review 1 |
| n245 | S4 | `plugins/suite` `update.py` blocked close | with `claude` and `git` both off PATH, update's blocked close gives Claude Code's address alone and says nothing of git; its other form says `install it` of several | read, not run | 2026-11-16, up4-update-close review 2 |
| n246 | S4 | `plugins/suite` `doctor.py` `close_command` | where the door's row is a warn with an install-cli remedy (an older door, none current at `~/.local/bin`), the close says `next: agentik setup` while the row and `--json` say install-cli; one line for both would read better | read, not run | 2026-11-16, dr1-door-ahead review 2 |

## From row tw1-test-walls (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n247 | S4 | `tests/test_agentik_suite.py` `walled` | under load the baseline run itself read 0.07 to 1.13 s, and a slow baseline loosens the bound: with a wall broken to 3.5 s one test passed once (3.57 s on a 1.06 s baseline); every stub sleeps 10 s or more, so a real break is caught; two baselines and the smaller of them would tighten it | review 1, L1 | 2026-11-17, tw1-test-walls review 1 |

## From packet ic2-needs (build 1, review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n248 | S4 | respeak's doctor's `fix:` for PyYAML | where `python3` on PATH is Homebrew's, `python3 -m pip install pyyaml` is refused by pip: that Python is externally managed; setup's step-1 warn names the need, no command | finding 7 of the first-install review; the `EXTERNALLY-MANAGED` file, read, not run | 2026-11-16, ic2-needs R1 |
| n249 | S4 | `plugins/suite` setup, doctor | ic2-needs' leads: a HOME set but not absolute plans; `update nosuch` calls it no plugin name; the doctor runs the 2 s need probe to drop it; all else done, the need shows in respeak's doctor alone; a shared need, a row a plugin (the lead of a name in the suite's old table alone went with the table, ak10c5-table-gone) | review 1 leads 2 to 8 | 2026-11-16, ic2-needs review 1 |
| n250 | S4 | `plugins/suite` `plan.py` `need_met` | PyYAML is read from the `python3` first on PATH alone, while respeak looks at several Pythons and one `RESPEAK_PYTHON` names, so the warn can stand where respeak works | review 1 F2, `python3.12` with yaml | 2026-11-16, ic2-needs review 1 |
| n251 | S4 | `plugins/suite` `doctor.py` `door()` | the door's rows whose remedy is `setup` (no `agentik` on PATH; an older one, the suite's command off PATH) say a bare `setup`, so with only a plugin outside the default set and such a door, the close installs the default set; `planned`'s words fit there | read, not run | 2026-11-17, ic2-needs review 2 L1 |

## From packet ak10b-term (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n252 | S4 | `scripts/sync` | a run interrupted between two placed files leaves the package half placed and a temp file, and the tree still passes the sums written before; lead: a `trap` that removes `*.sync.$$`, or the sums removed before the first place and written last | review 1 of ak10b-term | 2026-11-17, ak10b-term review 1 |
| n253 | S4 | `scripts/sync` | the seed's temp file, `messages.md.sync.$$`, has no leading dot; a kill before its rename leaves it in the package, where a later run keeps it and `install-cli` would freeze it; lead: `.messages.md.sync.$$` | review 1 of ak10b-term | 2026-11-17, ak10b-term review 1 |
| n254 | S4 | `scripts/sync` | where `agentik_term` or a placed name stands as a file, a folder or a dangling link, the run ends in exit 1 after part of the tree is written, a code the header does not list; lead: refuse with exit 2 before any write | review 1 of ak10b-term | 2026-11-17, ak10b-term review 1 |
| n255 | S4 | `scripts/sync` | a `plugin/lib/agentik_term` that is a link to a folder outside the tree is followed and written through; lead: refuse a link with exit 2 | review 1 of ak10b-term | 2026-11-17, ak10b-term review 1 |

## From row ak12-polish (the design's D7)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n257 | S4 | `plugins/suite` `completion.py` | a tool typed by its own name (`agentik-quill <Tab>`) is not completed: the scripts register `agentik` and `agentik-suite` alone; lead: register each `agentik-<tool>` the finder lists, its words from the cache | row ak12-polish D7 | 2026-11-19, ak12-polish |
| n258 | S4 | `plugins/suite` `completion.py` | `config <tool>.<Tab>` offers no key, since a tool's keys need its config read and so a process; lead: keep the keys of each config read beside the describe cache | row ak12-polish D7 | 2026-11-19, ak12-polish |
| n259 | S4 | `plugins/suite` `completion.py` | past a tool's first word nothing is offered, its second-level words and its flags included, since P10's `describe` carries first-level verbs alone | row ak12-polish D7 | 2026-11-19, ak12-polish |
| n260 | S4 | `plugins/suite` `completion.py` | no fish: `completion fish` is refused; lead: a third script on the same callback | row ak12-polish D7 | 2026-11-19, ak12-polish |

## From row hn1-help-next (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n261 | S4 | `plugins/suite` `status_read.py` `compose` | the status screen has no deadline over all its reads, so described `wall_s` of up to 10 s each can hold it for their sum; lead: one deadline over the screen's reads, as the inbox has | review 1 L2: 10.14 s with one read sleeping 9 s under a `wall_s` of 10 | 2026-11-20, hn1-help-next review 1 |

## From row rr7-way-in (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n262 | S4 | `scripts/sync` `table` | a private sync target with a regular `LICENSE` gets `SECURITY.md`, which points at a form its host does not serve for a private repo; lead: a rule for a public repo alone (a marker or a list) | review 1 F2: a private target's `--check` said `behind` and `unlisted` for both pages; the host's form read 404 there | 2026-11-20, rr7-way-in review 1 |
| n263 | S4 | `scripts/sync` `table` | the `LICENSE` test follows the volume's case: where it is case-insensitive a repo with only `license` gets both pages, where it is not, neither; lead: match the exact name | review 1 F5: a scratch repo with a file `license` held both pages after `sync` | 2026-11-20, rr7-way-in review 1 |
| n264 | S4 | `scripts/sync` `place` | `sync` overwrites a repo's own `CONTRIBUTING.md` without a word, and its stdout names no page; lead: name the two pages on the stdout line where it places them | review 1 F6: a hand-written page read `# Contributing` after `sync`, exit 0 | 2026-11-20, rr7-way-in review 1 |
| n265 | S4 | `scripts/sync` `--check` | a repo that drops its `LICENSE` keeps both pages: `--check` says `unlisted` for each, and the next `sync` makes it quiet with the pages still there; lead: `stale <page>` | review 1 F7: a second `sync` printed `every copy is commons'`, exit 0, both pages at the root | 2026-11-20, rr7-way-in review 1 |
| n266 | S4 | `scripts/sync` `place` | a folder at a destination (`CONTRIBUTING.md/`) ends the run in exit 1 and leaves `.CONTRIBUTING.md.sync.<pid>` and `scripts/.vendored.sync.<pid>`; lead: refuse a folder at a destination before any write | review 1 F8: `shasum: CONTRIBUTING.md: Is a directory`; a folder at `scripts/<x>` at the pin not checked | 2026-11-20, rr7-way-in review 1 |

## From row rc0-records-cut (build 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n267 | S4 | `scripts/records-cut` | a refused or failed move has no `--undo`: a failed commit leaves the staged removal and the copies, and its line names `git reset -q --hard HEAD` and the copies to remove; lead: an undo that checks the clone still stands at the cut's commit | packet rc0-records-cut R5 | 2026-11-20, rc0-records-cut |
| n268 | S4 | `tests/test_up2_suite_origin.py` | `test_12_the_printed_line_pulls_the_clone_and_runs_its_setup` fails now and then in a full `make check` (git clone into the temp origin: `failed to copy file`, or a hardlink differing from its source) and passes alone; lead: `--no-local` | gate 20261120-172023-2860 log; sitting 2026-11-18-2 | 2026-11-20, rc0-records-cut |

## From row rc0-records-cut (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n269 | S4 | `scripts/records-cut` | a stash or a local tag holding record changes past HEAD is not refused (`tips` reads branches and worktrees alone), so a later `stash pop` or `push --tags` brings a record back or publishes it | review 1 lead L1: a stash editing `HANDOFF.md` and a tag adding `bugs/t.md`, the dry run exit 0 | 2026-11-20, rc0-records-cut review 1 |
| n270 | S4 | `scripts/records-cut` | a linked worktree with an uncommitted record edit is not refused: the dirty check reads the main checkout alone | review 1 lead L2: an edited `HANDOFF.md` in a linked worktree, the dry run exit 0 | 2026-11-20, rc0-records-cut review 1 |
| n271 | S4 | `scripts/records-cut` `--go` | the repo's own commit hooks run during the cut's commit, and one may push, though the script never pushes; ruled: hooks stay on, as a refusing hook is how a failed step is tested | review 1 lead L5: a post-commit hook pushed a branch to the origin in a run that exited 0 | 2026-11-20, rc0-records-cut review 1 |
| n272 | S4 | `scripts/records-cut` | a record the clone ignores (untracked) stays in the clone and is not moved, so the move is not whole for it, though it is not public | review 1 lead L6: an ignored `history/private/n.md` left in the clone, absent at the destination, exit 0 | 2026-11-20, rc0-records-cut review 1 |
| n273 | S4 | `scripts/records-cut` `first_line` | a failed git step's line takes git's last stderr line, which with advice on is a `hint:`, not the cause | review 1 lead L8: `failed: git add .hygiene-allow: hint: Disable this message ...` | 2026-11-20, rc0-records-cut review 1 |
| n274 | S4 | `scripts/records-cut` | a kill partway leaves a state that a rerun refuses but cannot mend, and nothing prints the undo (see n267, no undo verb) | review 1 lead L9: killed after `git rm`, and after the commit, each rerun exit 2 with the key unset | 2026-11-20, rc0-records-cut review 1 |

## From row rc0-records-cut (review 2)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n275 | S4 | `scripts/records-cut` | a stale remote-tracking ref walks around the behind check: an unfetched record commit on the origin, `--go` exit 0, then the push is rejected; lead: `git ls-remote` against the upstream's sha (needs the network) | review 2 L1: `! [rejected] main -> main (fetch first)` | 2026-11-20, rc0-records-cut review 2 |
| n276 | S4 | `scripts/records-cut` the survey | an edit hidden by a `core.fsmonitor` hook reporting no change passes the survey; `--go` then loses it and fails half done; lead: `ls-files -f -v`, or `-c core.fsmonitor=false` on the status | review 2 L2 (a lying hook) | 2026-11-20, rc0-records-cut review 2 |
| n277 | S4 | `scripts/records-cut` the sums | the holder's `* text=auto` stores a CRLF record with LF ends; the sha256 proof reads the copy on disk, not what the holder stores; lead: `git hash-object --path` in the holder | review 2 L4, `history/crlf.md` | 2026-11-20, rc0-records-cut review 2 |
