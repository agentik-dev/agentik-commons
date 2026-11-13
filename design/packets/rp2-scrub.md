# Packet rp2-scrub: `scrub.py`, what leaves a free value before it is a draft, and the detector `send` runs

| item | value |
|---|---|
| from | agentik-hq's brief rp2 of 2026-11-13, R1 to R8; hq design/22 §3 items 4, 6, 7, 13 and §9; level S3 |
| pin | branch `rp1-shapes` at 23330e2 (in the landing queue); worktree `.claude/worktrees/rp2-scrub`, branch `rp2-scrub`; nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/scrub.py`; `tests/test_rp2_scrub.py`; this packet; `history/sittings/2026-11-13-19.md` |
| verify | `make check`, once, last, through the gate queue, `--strict` |
| acceptance | 1 to 12 below; `python3 -m unittest tests.test_rp2_scrub` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"...with warnings and ways to remove identifying or private information." An issue is public the moment it is filed. Three rows build beside this one: it touches only its two files.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names in fixtures and the packet).

- R1, what stands. One new module, `plugins/suite/lib/agentik_suite/scrub.py`, and its tests. It prints nothing. It imports `agentik_hygiene`, `os`, `re`, `subprocess` and `unicodedata` and nothing outside `STDLIB`. No tool's name stands in it: the public words reach it as data.
- R2, the signatures.
  - `machine(env, cwd, public, logins=()) -> m`. Reads, when called and writing nowhere: the home folder; the login; the host's short and full names; git's global `user.name` and `user.email` (one `git config` each, from PATH); the checkout root of `cwd` and its folder name; the user file's `checkouts`; the value, 8 bytes or longer, of each variable of `env` whose name holds `TOKEN`, `KEY`, `SECRET`, `PASS`, `AUTH` or `CREDENTIAL`; the scanner's `home`, `lan`, `secret` and `email` groups; the private list's rows, its path found from `env` by the scanner's own rule. `public` is `{"marketplace": NAME, "tools": {tool: "OWNER/REPO"}}`. `logins` are more names of kind `user`. A private list that exists and cannot be read raises `scrub.PrivateUnreadable`; no list is `m["private"] == "none"`.
  - `clean(text) -> text`: the design's 4(e).
  - `scrub(text, m) -> (text, counts, spans)`: `counts` is `{kind: n}`; `spans` is `[(start, end, kind)]` over the returned text, a placeholder's kind or `unsure`. It calls `clean` first and applies a pass to its own output until a pass changes nothing.
  - `detect(text, m) -> [kind]`: empty exactly when `scrub(text, m)[0] == text`; else the kinds a pass would replace, and `control` for a character `clean` would change. Kinds, never a match.
  - `strike(text, words, start=0) -> (text, places)`: each word, in any case and inside longer words, becomes `<struck-N>`, N going on from `start`; a word under four letters only as a whole word; a placeholder is never touched.
  - `weak(m) -> [kind]`: the kinds of machine name that are public words on this machine.
- R3, a pass, in this order: `clean`; each `%XX` of a printable ASCII character decoded, until stable; the named variables' values; a key block from its `BEGIN` line through its `END` line and three or more lines of bare base64; URLs and scp-form remotes; the name words before a bracketed email, then emails; paths; the assignment rule; machine names; the scanner's four groups; the private rows; addresses; sites; long runs. A placeholder already in the text is sealed before the pass and written back after it, and numbering goes on after the highest N of its kind. One value gets one placeholder for the whole text, whatever its case.
- R4, paths: the design's 4(b), every clause. A path is kept only when the whole of it is one of the closed list's forms, matched by segments; a `.` or `..` segment is never kept; a public tool's config, cache or state folder keeps its head and gives its tail a `<path-N>`. A replaced path takes the rest of its quoted string, else the words after it through the last one that holds a slash and on to a stop. The home folder counts in any case, by its real path, and under the two system prefixes.
- R5, machine names: the design's 4(a). A name of three letters or more is replaced as a whole word, a word ending at any character that is not a letter; inside a longer word it is a span of kind `unsure`. A name that is a public word is replaced only beside `@`. The public words are the placeholders' kinds, every name of `public` (each tool, `agentik`, `agentik-<tool>`, each owner and repo) and two tuples the caller may extend: the suite's verbs and the twelve programs of 4(b).
- R6, the reporter's own shapes: the design's 4(c), second half. A number is no secret: `tokens: 4096` and `input_tokens=1200` stay.
- R7, the placeholders, a closed set: `<path-N>`, `<user>`, `<host>`, `<repo>`, `<project>`, `<secret>`, `<email-N>`, `<address-N>`, `<private-N>`, `<struck-N>`, `<name-N>`, `<url-N>`, `<site-N>`, `<run-N>`. A private row's term is in no output, no exception and no log.
- R8, the fixtures. Every hostile line is assembled at run time from parts, a made-up marker in each private place, so the scanner's scan of this repo counts nothing new and `.hygiene-allow` is not touched. A machine is made by hand for a test; no test reads the real home, login or private list.

## 3. Acceptance

Measured at 23330e2: `scrub.py` does not exist, so every line of 1 to 11 fails on its import; `scripts/hygiene --json` in the worktree: every group's `outside_lines` is 0.

| # | line |
|---|---|
| 1 | paths: for each case of 4(b) (spaces, quoted and not; `--flag=path`; a `PATH`-like list; relative; one segment; a last folder name with a space; the home in upper case, under the data volume, percent-encoded, as a file URL, dashed with and without a tail): no marker, one `<path-N>` or `<project>` where the path stood |
| 2 | kept by name: each form of the closed list unchanged; a private plugin's folder, a private script beside the launchers, a private formula, a private state root and a climb by `..` out of a kept tree leave no marker; a public tool's state folder with a private tail is the folder and `<path-1>` |
| 3 | the tail's words: `loading <a path> failed at line 9` keeps ` failed at line 9`; `fatal: <a path whose last folder is three words> is not a git repository` keeps ` is not a git repository` and no word of the folder |
| 4 | machine names: the login as a word, before a digit, before `_`, in `uid=501(...)`, beside `@`, in full-width letters and with a zero-width space inside: gone each time; inside a longer word: one `unsure` span and no replacement |
| 5 | plain words: for logins `user`, `path`, `host`, `git`, `claude`, `doctor` and a made-up public tool, and a checkout folder `agentik-<tool>`: `agentik <tool> doctor` unchanged, `owner <login> on box` keeps it, `<login>@box` loses it, `weak(m)` names the kind |
| 6 | secrets and names: a 23-line key block gives one `<secret>` and no line of its body, whole and with its first three lines cut; a URL with userinfo, an scp-form remote, a database URL, a bearer and a basic header, three assignment forms, a trailer's two name words, a percent-encoded email, a public quad, an IPv6, a MAC and an internal host: no marker, no run of 19 characters or more |
| 7 | left as they are: `tokens: 4096 of 8192`, `at 12:34:56`, `agentik.doctor/1 read/write and/or 3/22 checks`, a public repo's issue URL, a test's name of 45 letters and underscores, a 12-hex commit, `README.md, setup.sh, main.py` |
| 8 | the fixed point: for every line of 1 to 7 and 3,000 lines glued at random (seeded) from their pieces, `scrub(scrub(x)[0])[0] == scrub(x)[0]` and `detect(scrub(x)[0], m) == []` |
| 9 | `clean`: a carriage return's overwritten line comes back as two lines, an erase-line sequence goes whole, six format characters go; `detect` of the raw line holds `control` |
| 10 | `strike`: `path`, `details`, `1` and `art` over a text holding `<path-1>` and `Art` beside `artisan`: `<path-1>` whole each time, `art` strikes the whole word only |
| 11 | no private term: with a list of three made-up rows, no row's term in any return value or raised message; an unreadable list raises `PrivateUnreadable` |
| 12 | `make check`, once through the gate queue, green; `scripts/hygiene` counts what it counted at the pin |

## 4. Not built

The gather, the form, the send and the verb (other rows). A token shape for the scanner (rp1). Look-alike letters of another script, and a token a tool broke across two lines: the design names both as left.

## 5. The landing

`plugin.json` stays as it is: rp6 takes the version. Phase 2 merges main after rp1-shapes lands, on the coordinator's word.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, a relay ledger. The report: head sha, the gate's id and exit, acceptance 1 to 12 at the pin and now.
