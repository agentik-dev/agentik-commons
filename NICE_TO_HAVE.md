# Nice to have

Findings that block nothing, one row each, in hq design/05 §2's table; `scripts/recordlint` holds it. The list before 2026-11-01 is frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet that touches an area greps them by path.

## Open

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n174 | S4 | `plugins/suite` `plan.py` step 3, `cli.py` `_not_a_verb` | a tool with a `page` and a held or unfound source: setup's plan shows step 3's lone row, no step 4 or 7 row and never the page, while `T doctor` refuses with the page | review 1 lead, homes hB, hH, pC | 2026-11-14, fh13-relay-plan fix of review 1 |
| n175 | S4 | `plugins/suite` `plan.py` step 4, `cli.py` `_not_a_verb` | a tool with a `page` whose command a fork or the plugin's root holds: step 4 says `T installed its own command, at ...`, while `T doctor` says `T is a plugin with no command` (the pin's refusal, as R8 rules); one wording for both | review 1 lead, homes hD, hJ, pA, a root's `bin/` | 2026-11-14, fh13-relay-plan fix of review 1 |
| n172 | S4 | `plugins/suite` the refresh at SessionStart | the refresh at SessionStart moves only a launcher whose tree its own plugin froze: not held by fk2-plan, so an enabled copy numerically newer can still replace a fork's launcher | hq design/25 §3 item 16, R1-F2 | 2026-11-14, fk2-plan build 1 |
| n173 | S4 | `tests/test_agentik_suite.py` `WallTest.test_f2_twenty_slow_tools_add_nothing_past_the_wall` | n171's 3.0 s bound in a second test: `config` took 3.02 s at load 8 beside another check, and was green alone three times at the same head; one bound for both tests, widened or measured against an idle baseline | gate 20261114-061401-1894 | 2026-11-14, fh13-relay-plan build 1 |
| n104 | S4 | `plugins/suite` `config.py`, `scripts/voice` | `describe sources T extra` names `describe` alone; a TOOL of `""` or `suite` reads `absent`; voice says `line 0` for an unreadable user file | notes 9, 10 | 2026-11-13, fk1 review 1 |
| n103 | S4 | `plugins/suite` `sources.py` `entries` | the v1 dict shape of `installed_plugins.json` reads `absent`, as `plan.py` does | note 8 | 2026-11-13, fk1 review 1 |
| n102 | S4 | `plugins/suite` `sources.py` `read` | an entry whose folder is gone stands `found`, where `plan.py` reads it not installed | note 7, read only | 2026-11-13, fk1 review 1 |
| n101 | S4 | `plugins/suite` `sources.py` `mirror` | an `agentik` source that is no mapping reads `mirror` false; R8 may mean true | note 6 | 2026-11-13, fk1 review 1 |
| n100 | S4 | `plugins/suite` `sources.py` `_runs` | an unset or empty PATH reads `.`, so a stray `./agentik-T` runs as `placed`; R6 copies `doctor.first_door` | note 5, p4 S7 | 2026-11-13, fk1 review 1 |
| n99 | S4 | `plugins/suite` `sources.py` `whose` | a `projectPath` of `.` or `""` is read against the process cwd, so it is the repo's from any folder | note 4, p4 S8 | 2026-11-13, fk1 review 1 |

## From packet ak3p (the join of ak2b-reach, ak3-setup and ak3d-doctor)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n76 | S3 | `plugins/suite` `settings.py` `read` | a FIFO at the user settings file hangs `doctor` and `status --check` with no deadline: the read opens it; refuse a file that is not regular, as `read_regular` does for the plan's reads | ak3d review 1's R1-F1: doctor past 15 s; the same read ak2b fix round 1 left alone | 2026-11-13, ak3d review 1 |

## From packet rp1-shapes (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n95 | S4 | `design/packets/rp1-shapes.md` | the review's acceptance read: 1 held bare only (R1-F1), 2, 3, 5 and 6 hold, 4 holds with the copy at 100644, 7 rests on the build's gate | review 1's N8 | 2026-11-13, rp1 review 1 |
| n96 | S4 | `scripts/hygiene` JWT | each part opens `eyJ`, three letters where the brief says six, a superset; an unsigned JWT (`header.payload.`, empty signature) counts 0 | review 1's N9 | 2026-11-13, rp1 review 1 |
| n97 | S4 | `scripts/hygiene` | a token split across a line end counts 0, but a project key whose first half is 20 characters or more; the design's item 13 accepts this | review 1's N10 | 2026-11-13, rp1 review 1 |
| n98 | S4 | `scripts/hygiene` `secret` | a lead for rp2: GitLab's `glpat-<body>.01.<suffix>` form counts 1 but the match ends at the first `.`, so a scrub of the match alone leaves the suffix | review 1's N11 | 2026-11-13, rp1 review 1 |

## From packet sc10-doctor-checks (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
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

## From packet rp3-gather (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n118 | S4 | `plugins/suite` `doctor.py` details | the doctor's `doctor.tool.*` detail takes the last line of a tool's own doctor output whole, and the `shadow` and `plan` details hold paths; free by R4 and kept by `gather`, so rp2's scrub is their only guard: a line for rp2's or rp6's review | review 1's first note, read | 2026-11-13, rp3 review 1 |
| n119 | S4 | `gather.py` `_entry` | takes the first install of a key's list, so with several scopes (a project-scoped install first) the version shown may be another folder's; it does not change with the working folder | review 1's note; read, not verified on a real file | 2026-11-13, rp3 review 1 |
| n120 | S4 | `gather.py` `_launcher` | an unreadable launcher (mode 000) reads None, as an absent one does, not `unreadable`: `read_regular` gives None for both | review 1's note; read, not probed | 2026-11-13, rp3 review 1 |
| n121 | S4 | `gather.py` `_installed` | reads `installed_plugins.json` with no size limit (`read_regular`, limit -1), so a huge file costs memory | review 1's note; read, not probed | 2026-11-13, rp3 review 1 |
| n122 | S4 | `gather.py` `bound` | assumes `map_free`'s `fn` gives text: a None in a row's name, detail or a line raises in `_cut`, and a lone surrogate raises `UnicodeEncodeError`; the join's contract | review 1's note; read, not run | 2026-11-13, rp3 review 1 |
| n123 | S4 | `gather.py` `facts` | catches `Exception` from `read_doctor`, so a `SystemExit` raised by an in-process doctor passes through; the join's concern | review 1's note; read | 2026-11-13, rp3 review 1 |
| n124 | S4 | `gather.py` `system` | a release of dots alone (`...`) is kept as it is; only one with no leading digit or dot reads `unreadable`; cosmetic | review 1's note; read | 2026-11-13, rp3 review 1 |
| n125 | S4 | `gather.py` version patterns | `VERSION` and `CLAUDE` admit up to 36 freely chosen digits (`[0-9]{1,9}` three times and an rc number), a side channel in theory only | review 1's note; read | 2026-11-13, rp3 review 1 |
| n126 | S4 | commits | each commit's author line carries the account's git identity; the repo's practice, not one slice's | review 1's note | 2026-11-13, rp3 review 1 |

## From packet rp4-form (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n127 | S4 | `plugins/suite` `form.py` `nothing_new` | the known words come from `build`'s bytes, where a cell's pipe is written escaped, so a render quoting a check's detail that holds a pipe misses on a word the draft holds and falls back to the template; read the escape back first | review 1's R1-F4, probe p5 | 2026-11-13, rp4 review 1 |
| n128 | S4 | `plugins/suite` `form.py` | GitHub's own drawing of the form is not verified: pandoc's GFM stands in; a placeholder inside a code span, a title's `#12` or backticks on GitHub are the look the row owes | review 1's note 1, probe p2 | 2026-11-13, rp4 review 1 |
| n129 | S4 | `plugins/suite` `form.py` | a bidi control (U+202E) in a value is accepted and drawn inside `<code>`, its reordering of the labels after it in a browser unverified; NUL, ESC and other C0 controls read back, NUL drawn as U+FFFD; their removal is rp2's and rp5's | review 1's note 2 | 2026-11-13, rp4 review 1 |
| n130 | S4 | `plugins/suite` `form.py` `title` | the title is cut on a code point, not a grapheme: a flag pair is split, a ZWJ sequence left ending in ZWJ, a combining accent dropped from its letter; R5's character edge is met | review 1's note 3, probe p7 | 2026-11-13, rp4 review 1 |
| n131 | S4 | `plugins/suite` `form.py` `title` | the verb is compared case-sensitively: `title("doctor", "Doctor: failing")` gives `doctor: Doctor: failing` | review 1's note 4 | 2026-11-13, rp4 review 1 |
| n132 | S4 | `plugins/suite` `form.py` `subject` | digits leave a check's name too, so `py39` and `py312` give one fingerprint (design item 11); no command and no row of the tool gives `check:<tool>::`; a `ran` of spaces gets a check subject while the form writes `(empty)` | review 1's note 5, probe p4 | 2026-11-13, rp4 review 1 |
| n133 | S4 | `plugins/suite` `form.py` `nothing_new` | by the rule's letter a new sentence's opener (`The`, `It`) misses unless the form holds the word, `e.g.` misses, a possessive of a hyphened word misses; a lowercase name, a ZWJ-joined one or a backslash path passes and `added` lists it | review 1's note 6, probe p5 | 2026-11-13, rp4 review 1 |
| n134 | S4 | `plugins/suite` `form.py` `fit` | a fit that drops every row (all `warn`) leaves an empty table under a summary that still counts them; a form of exactly 4,096 bytes stays, as `send`'s ceiling reads it | review 1's note 7, probe p6 | 2026-11-13, rp4 review 1 |
| n135 | S4 | `plugins/suite` `form.py` `draft` | a plugin's version is not normalised: `1.2` gives fields that `build` refuses (`field plugins`); gather does not say it normalises plugin versions, so the join should check | review 1's note 8 | 2026-11-13, rp4 review 1 |
| n136 | S4 | `plugins/suite` `form.py` `parse` | every name of the Versions line, the Plugins line and the rows is checked against `tools`, so `send` passes the public tools with `suite` and `door`; the first build's decide line | review 1's note 9 | 2026-11-13, rp4 review 1 |
| n137 | S4 | `plugins/suite` `form.py` `put` | `put` takes `rows.01.name` as row 1, a key `free` never lists | review 1's note 10 | 2026-11-13, rp4 review 1 |

## From packet rp2-scrub (review 1)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n138 | S4 | `scripts/hygiene` `lan`, `email` | quadratic on a long dashed run with a `.`: 0.55 s at 10 KB, 13.1 s at 40 KB; nearly every text holds a `.`, so the scrub's gate rarely skips `lan` | review 1's notes; 0.60 s at 10 KB on the fix | 2026-11-13, rp2 review 1 |
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
| n154 | S3 | `plugins/suite` `cli.py` `_takes` | a mended `config` line is still refused for a second wrong word: `confg x` gives `config x`, which pasted reads `x is not a tool here`, exit 2 (55 lines of the sweep); `offer` could check the first name against the tools and plugins | review 2's F2 | 2026-11-13, sc4 review 2 |
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
