# Packet rp3-gather: `gather.py`, a closed list of typed facts, and `public.json`, the tools an issue may name

| item | value |
|---|---|
| from | agentik-hq's brief rp3 of 2026-11-13, R1 to R7; hq design/22 §3 items 2, 3 and 13, §9 (R1-F8); level S3; a row of the suite's issue reporter, built beside rp2, rp4 and rp5 |
| pin | agentik-commons branch `rp1-shapes` at 23330e2 (the setup and doctor join, suite 0.6.x, and the scanner's copy); worktree `.claude/worktrees/rp3-gather`, branch `rp3-gather`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test reads the real home, doctor or plugin list; made-up names |
| may touch | `plugins/suite/lib/agentik_suite/gather.py`; `plugins/suite/lib/public.json`; `tests/test_rp3_gather.py`; `.hygiene-allow` (one row, after the row of `fallback.json`); this packet; `history/sittings/2026-11-13-20.md` |
| verify | `make check`, once, last, through the gate queue, `--strict` |
| acceptance | 1 to 12 below; `python3 -m unittest tests.test_rp3_gather` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"...submits issues to github with relevant info to diagnose on this computer..." Relevant means a closed list: each fact has a type and a bound, and nothing else is read. Three builders work beside this one from the same pin (`scrub`, `form`, `send`); each touches only its own files.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names in fixtures and the packet).

- R1, what stands. New: `plugins/suite/lib/agentik_suite/gather.py`, `plugins/suite/lib/public.json`, `tests/test_rp3_gather.py`, one row of `.hygiene-allow`. The module prints nothing, holds no catalogue id and imports nothing outside `STDLIB`. No tool's name stands in the module or its tests: names reach it from `public.json`, and a test's public table is made up.
- R2, `public.json`: `{"marketplace": NAME, "tools": {tool: "OWNER/REPO"}}`, the name and each plugin of `.claude-plugin/marketplace.json`, the repo read from the plugin's source URL. A test holds the two equal in that sense. `.hygiene-allow` gains one row for it, group `sibling`, under one line of reason, after the row for `fallback.json`. `load_public(lib) -> public` reads it and raises `ValueError` on any other shape. Nothing reads the machine's own marketplace file for this.
- R3, the signatures, which the join calls as written. `facts(env, lib, given, read_doctor) -> facts`, `given` being `{"tool", "ran", "exit", "output", "expected"}` (a name, text, an int, a file's path, text; each may be None) and `read_doctor()` an `agentik.doctor/1` object or None. `bound(facts) -> facts`: R5's bounds on free values, after the caller's scrub; a cut falls on a character's edge and never inside a placeholder. `map_free(facts, fn) -> facts`: `fn` over every free value, in a fixed order.
- R4, the object, `agentik.issue-facts/1`: `schema`, `tool`; `versions` `[{name, plugin, commit, launcher}]`; `system` `{os, release, arch, python, claude, where}`; `checks` `{read, rows: [{tool, status, name, detail}], failed, warned, passed}`; `plugins` `{named: [{name, version}], others}`; `output` `{ran, exit, lines}`; `words` `{expected}`. Free: a row's `name` and `detail`, `ran`, each of `lines`, `expected`. Every other value is typed.
- R5, sources and bounds. `versions`: the suite, then `door`, then each tool of `public` by name; `plugin` and `commit` from `installed_plugins.json` (`version`, `gitCommitSha` cut to 12), `launcher` from the first `agentik-<tool>` on PATH that is a regular file, by `read_launcher`; a version is `N.N.N` with at most one of `-alpha.N`, `-beta.N`, `-rc.N`, a commit 12 hex, anything else `unreadable`, an absent one None. `system`: `os` `Darwin`, `Linux` or `other`; `release` the leading digits and dots of `os.uname().release`, 20 bytes; `arch` `arm64`, `x86_64`, `aarch64` or `other`; `python` from `sys.version_info`; `claude` the first `N.N.N` of `claude --version` from PATH under 5 s, else `unreadable`; `where` `in Claude Code` when `CLAUDECODE` is in `env`, else `at a terminal`. `checks`: from `read_doctor()`; a row is a `fail` or `warn` check of the suite's group or a group whose tool is in `public`, `fail` rows first; every other check, a tool outside `public`'s included, joins `passed`, and such a tool is never named; an unlisted key reaches nothing; no object or another schema: `read` false, rows empty; 12 rows, a name 60 bytes, a detail 200. `plugins`: each installed plugin of `public`'s marketplace whose name is in `public`, by name and version, 12 at most; every other as one count. `output`: `ran` 200 bytes; `exit` 0 to 255; `lines` the last 200 lines of the file's last 64 KiB, bad bytes replaced, `bound` keeping the last 20, each 200 bytes. `words`: `expected`, 600 bytes.
- R6, never read: a transcript, a prompt, a session's id, a ledger, a `CLAUDE.md`, a charter or any file of a repo, a repo's name or path, the working folder, `PATH`'s value or any other environment value, a settings or state file's content, a key or a token. `facts` takes no `cwd`.
- R7, not this row's: `doctor.py`, `cli.py`, `messages.md`, `tools.py`, `plan.py`, `README.md`, `plugin.json`, `tests/test_agentik_suite.py`.

## 3. Acceptance

Each in the suite tests' `Home`, a stub `claude` that prints a version, every tool made up but in line 1. Measured at 23330e2: the package holds no `gather.py` and `plugins/suite/lib/` no `public.json`; the doctor's object holds no OS, no exit code and no version as a field; `scripts/hygiene --json`: `sibling` `outside_lines` 0 (118 lines, all allowed).

| # | line |
|---|---|
| 1 | `load_public(lib)` equals what `.claude-plugin/marketplace.json` gives: its name, and for each plugin the `OWNER/REPO` of its source URL; a `public.json` with a key added or a repo with a third segment raises `ValueError` |
| 2 | `scripts/hygiene --json` in the worktree: `sibling`'s `outside_lines` equals the pin's (0), `public.json` allowed by its row |
| 3 | a doctor fixture with 30 failing checks, a detail of 5,000 bytes and a check's name of 300: after `bound`, 12 rows, `fail` before `warn`, a name of 60 bytes at most, a detail of 200; `failed`, `warned` and `passed` count all 30 and the rest |
| 4 | a fixture with a group for a tool outside `public`, one check failing: its name is in no value of `facts`, its checks are in `passed`, `failed` does not count it |
| 5 | an installed plugin outside `public`: `plugins.others` is 1 and its name is in no value |
| 6 | a launcher whose `VERSION` is a branch's word, and a plugin entry whose version is 60 letters: each reads `unreadable` |
| 7 | a marker in an environment value, the working folder's name, a `CLAUDE.md` there and the user settings file: `json.dumps(facts)` holds it nowhere |
| 8 | an output file of 3 MiB whose last line is known: `lines` holds 200, the known one last; after `bound`, 20 lines of 200 bytes at most; a line cut inside `<path-12>` ends before it |
| 9 | `CLAUDECODE=1` in `env`: `where` is `in Claude Code`; without it, `at a terminal`; no `claude` on PATH: `claude` is `unreadable`, and the call returns inside 6 s |
| 10 | `read_doctor` returning None, and an object of another schema: `checks.read` false, rows empty, the rest of `facts` whole |
| 11 | after lines 3 to 10: HOME unchanged, and the stub `claude` recorded one call, `--version` |
| 12 | `make check`, once through the gate queue, green |

## 4. Not built

A hook's event and a resolved profile's keys (ruled out by design/22 by name). The scrub of a free value, the form, the send, the verb and its questions (rp2, rp4, rp5, rp6). One fork is the owner's, design/22 §6 question 1 (where an issue is filed); this row builds its recommended answer, a repo for each tool.

## 5. The landing

`plugin.json` stays as it is: rp6 takes the version. The join passes `read_doctor` as a function that runs the doctor verb in process.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, a relay ledger, the machine's own plugin files. The report: head sha, the gate's id and exit, acceptance 1 to 12 at the pin and now.
