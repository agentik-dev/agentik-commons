# Packet rp8-respeak: `issue new --render`, the narrator's script at a terminal, with the template as the floor

| item | value |
|---|---|
| from | agentik-hq's brief rp8 of 2026-11-14, R1 to R6, and the coordinator's start line; hq design/22 §2 item 5, §3 item 10, §6 question 3 (the recommended answer), §9's R1-F11; level S3; the eighth row of the suite's issue reporter |
| pin | main at 9cc01aa (suite 0.7.3, rp6-verb and in4-inbox landed); worktree `.claude/worktrees/rp8-respeak`, branch `rp8-respeak`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test runs the real `claude`, the real narrator script or a model, or reads or writes the real home; nothing written in the narrator's repo; made-up names; no version (the start line replaces R6's patch version: a phase 2 names it) |
| may touch | `plugins/suite/lib/agentik_suite/render.py` (new), `plugins/suite/lib/render.json` (new), `tests/test_rp8_render.py` (new); `issue.py` (the lines of `new` that call the render, and `reword`'s road shared with them); `cli.py` (one flag); `messages.md` (`flag.render`, the render's lines at the end of `## Issue`); `design/voice/checked.sha256`; `.hygiene-allow` (one row, `render.json`); `README.md` (one paragraph); `NICE_TO_HAVE.md` (a row, if one is found); this packet; `history/sittings/2026-11-14-4.md`. Not this row's: `scrub.py`, `gather.py`, `form.py`, `send.py`, the skill, `plugin.json`'s version |
| verify | `make voice`, then `make check`, each once, last, through the gate queue, `--strict` |
| acceptance | 1 to 9 below; `python3 -m unittest tests.test_rp8_render` OK |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The owner's words

"Issues should be concise, done via respeak, and approved by the user submitting the issue." The form is concise without a model. The narrator renders two lines of it, `Happened` and `Expected`, and a render that brings in a word the scrubbed draft did not hold is dropped for the words as typed.

## 2. Rulings

The repo keeps no `DECISIONS.md` and no `CLAUDE.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names in fixtures and this packet).

- R1, what stands. New: `plugins/suite/lib/agentik_suite/render.py`, `plugins/suite/lib/render.json`, `tests/test_rp8_render.py`. No tool's name stands in the package, its catalogue or the tests: the narrator's name is data in `render.json`, which takes one row of `.hygiene-allow`, group `sibling`, under one line of reason. The flag is `--render`.
- R2, `render.json`: `{"plugin": NAME, "script": "scripts/respeak-render.sh", "mode": "technical"}`. A test holds that `NAME` is a tool of `public.json`.
- R3, `render.py`. `find(env, lib) -> path or None`: the script under the install path of `NAME@<marketplace>` in Claude Code's `installed_plugins.json`, a regular executable file, else None. `run(script, data, env, wall=600) -> {"happened", "expected"} or None`: an empty temporary folder; the draft's bytes written there as the source and the contract as a second file; the script started with that folder as its working folder, `--mode`, `--source`, `--out` and `--contract`. The contract's text is a catalogue message: technical, two sentences a line, error text verbatim, nothing added, the answer as two lines, `Happened: ...` and `Expected: ...`. An exit that is not 0, no output file, a file that is not those two lines, or the wall passed gives None, and the child's group is ended. The folder is removed either way. The script's own stdout and stderr are not shown.
- R4, `new --render`, in `issue.py`: after the draft is written, `find`; none is one line saying the template stands and why, exit 0. Then `run`; None is the same line with its reason. A render then takes `reword`'s own road, with no second copy of it: `form.nothing_new`; a miss leaves the template and says so; a pass puts the two values, runs layer 1 over them again and lists the added words as unsure. The draft printed at the end is the one on disk. Off a terminal the flag works the same; nothing prompts.
- R5, the render reads only what an issue could hold: the source is the scrubbed draft. The README's paragraph says what the design measured: the narrator's tools reach the disk and a headless run under a login loads the user's CLAUDE.md, which is why the check exists.
- R6, `cli.py`: `--render` in the verb's flag tuple, one line; the frame takes it for `issue` and `issue.py` refuses it, in sc4's two lines, for every word but `new` (the start line). `messages.md`: `flag.render` in `## Help`, the render's lines at the end of `## Issue`.

## 3. Acceptance

Measured at 9cc01aa: `agentik-suite issue new --render` prints `FAIL  --render is not a flag of issue` and `next: ... help issue`, exit 2; `issue send --dry-run --render` the same. `scripts/hygiene`: `sibling` 149 lines in 41 files, 0 outside the allowlist. The real script (read, not run): `--mode M --source F --out F [--contract F]`; exit 0 a passing render, 1 the gate still failing, 2 a refusal or a setup or runner failure or its wall, 4 an account failure; it starts `claude -p` for up to 600 s and reads a corpus of 45,641 bytes.

Each line in `ConfigHome` with a made-up narrator plugin installed there, its script a stub that records its argv and working folder and writes a canned answer; no test starts `claude` or the real script.

| # | line |
|---|---|
| 1 | `issue new <tool> --ran ... --expected ... --render` with a stub whose answer is a clean paraphrase: exit 0; `issue.md`'s two values are the stub's; the added words are listed as unsure; the file reads back as the form |
| 2 | a stub whose `Expected` line adds a capitalised name the draft does not hold: exit 0, `issue.md` holds the words as typed, and one line says the render was dropped; the name is in no file and no stream |
| 3 | a stub that drops the draft's placeholder, and one that drops the error text: the template stands each time |
| 4 | no narrator plugin installed: the template and one line naming the reason; a stub that exits 1: the same; in process with the wall shortened, a stub that sleeps: the same inside the wall, its group gone |
| 5 | the stub's record: its working folder held two files and no other, the source's bytes equal the draft's, and the folder is gone afterwards |
| 6 | a marker planted in the working folder's name and in an environment value: not in the source file the stub saw |
| 7 | `issue new` without the flag: the stub recorded no call |
| 8 | `help issue` lists `--render`; `issue send --render` and `issue discard --render` are refused in the frame's two lines; `scripts/hygiene`'s `sibling` count outside the allowlist equals the pin's |
| 9 | `make voice`, then `make check`, each once through the gate queue, green |

## 4. Not built

The skill's road in a session, which rp6 built. A render started by default, and the narrator in the suite's default set: owner question 3's other answers. A timed real render: the owner's hand, after the landing. The version: a phase 2.
