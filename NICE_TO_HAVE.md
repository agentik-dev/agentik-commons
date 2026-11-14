# Nice to have

Findings that block nothing, one row each, in hq design/05 §2's table; `scripts/recordlint` holds it. The list before 2026-11-01 is frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet that touches an area greps them by path.

## Open

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n104 | S4 | `plugins/suite` `config.py`, `scripts/voice` | `describe sources T extra` names `describe` alone; a TOOL of `""` or `suite` reads `absent`; voice says `line 0` for an unreadable user file | notes 9, 10 | 2026-11-13, fk1 review 1 |
| n103 | S4 | `plugins/suite` `sources.py` `entries` | the v1 dict shape of `installed_plugins.json` reads `absent`, as `plan.py` does | note 8 | 2026-11-13, fk1 review 1 |
| n102 | S4 | `plugins/suite` `sources.py` `read` | an entry whose folder is gone stands `found`, where `plan.py` reads it not installed | note 7, read only | 2026-11-13, fk1 review 1 |
| n101 | S4 | `plugins/suite` `sources.py` `mirror` | an `agentik` source that is no mapping reads `mirror` false; R8 may mean true | note 6 | 2026-11-13, fk1 review 1 |
| n100 | S4 | `plugins/suite` `sources.py` `_runs` | an unset or empty PATH reads `.`, so a stray `./agentik-T` runs as `placed`; R6 copies `doctor.first_door` | note 5, p4 S7 | 2026-11-13, fk1 review 1 |
| n99 | S4 | `plugins/suite` `sources.py` `whose` | a `projectPath` of `.` or `""` is read against the process cwd, so it is the repo's from any folder | note 4, p4 S8 | 2026-11-13, fk1 review 1 |

## From packet ak3p (the join of ak2b-reach, ak3-setup and ak3d-doctor)

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n70 | S4 | `plugins/suite` `apply.py` `execute` | a command that exits 0 but leaves a child holding stdout is held to the wall (600 s for `claude`) and then reads failed; a daemon that leaves the group lives on; whether the real `claude` does this is not known | ak3-setup review 1's R1-F7, not seen with the real `claude` | 2026-11-13, ak3-setup review 1 |
| n71 | S4 | `plugins/suite` `apply.py` | no lock: two setups at once each run every command and each claims the other's writes; an exclusive `flock` beside the journal for the run | ak3-setup review 1's R1-F8: two runs, every call twice | 2026-11-13, ak3-setup review 1 |
| n72 | S4 | `plugins/suite` `apply.py` `--json` | a refusal (`needs_yes`, `gated`, `blocked`, `declined`) prints the error object alone, without `steps`, `ran`, `wrote`, `nothing`, `journal`, which a failed step keeps | ak3-setup review 1's R1-F9; the builder's choice | 2026-11-13, ak3-setup review 1 |
| n73 | S4 | `plugins/suite` `apply.py` `run` | an interrupt after `execute` returns and before `current` clears records a finished command as stopped; one inside `record` reads between steps and can leave it out of `ran` | ak3-setup review 2's N1, not confirmed | 2026-11-13, ak3-setup review 2 |
| n74 | S4 | `plugins/suite` `apply.py` | SIGTERM ends setup with exit 130, SIGINT's code; a caller's script expects 143 | ak3-setup review 2's N2 | 2026-11-13, ak3-setup review 2 |
| n75 | S4 | `plugins/suite` `apply.py` `run` | after the first interrupt both signals stay ignored until `run` returns, so a second Ctrl-C cannot end a last `plan.build` that hangs; whether each read there has its own bound is not checked | ak3-setup review 2's N3 | 2026-11-13, ak3-setup review 2 |
| n76 | S3 | `plugins/suite` `settings.py` `read` | a FIFO at the user settings file hangs `doctor` and `status --check` with no deadline: the read opens it; refuse a file that is not regular, as `read_regular` does for the plan's reads | ak3d review 1's R1-F1: doctor past 15 s; the same read ak2b fix round 1 left alone | 2026-11-13, ak3d review 1 |
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
