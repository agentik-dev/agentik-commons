# Packet rp5-send: the last check, the screen that is the bytes, the typed word and the one door to `gh`

| item | value |
|---|---|
| from | agentik-hq's brief rp5 of 2026-11-13, R1 to R10; hq design/22 §3 items 7, 8, 9, 11, 12 and 16, §9 (R1-F1, F5, F9, F10, F14, F16); level S3; the fifth row of the suite's issue reporter |
| pin | branch `rp1-shapes` at 23330e2 (reviewed, not yet on main); worktree `.claude/worktrees/rp5-send`, branch `rp5-send`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test sends to a real service, opens a browser, runs the real `gh` or reads the real home; made-up names; no version set |
| may touch | `plugins/suite/lib/agentik_suite/send.py`; `tests/test_rp5_send.py`; `plugins/suite/lib/agentik_suite/messages.md` (a new last section `## Issue` alone); `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-13-22.md` (the first build) and `history/sittings/2026-11-13-28.md` (the fixes of reviews 1 and 2, and phase 2) |
| verify | `make voice`, then `make check`, each once, last, through the gate queue, `--strict` |
| acceptance | 1 to 12 below; `python3 -m unittest tests.test_rp5_send` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"...and approved by the user submitting the issue." Approved means a person read the exact bytes on a terminal and typed a word; a model drafts, and a person sends. Three rows build beside this one from the same pin (`scrub`, `gather`, `form`); this row touches only the files named here.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names in fixtures and the packet). `send` is the design's stated exception to three of the command's own principles: it refuses `-y`, it prompts on the terminal device whatever stdin is, and it starts `gh`.

- R1, what stands. New: `send.py`, `tests/test_rp5_send.py`, a last section `## Issue` in `messages.md` and its sidecar from `make voice`. The module imports `hashlib`, `os`, `subprocess`, `signal`, `time` and nothing outside `STDLIB`; no `pty`, `termios` or `urllib`. No tool's name in it, its messages or its tests; "inside Claude Code". It imports no module of the three rows beside it.
- R2, the last check. `check(data, m, public, form, scrub, ceiling=4096) -> [(line, kind)]`, empty when the draft may be shown. `form.parse(data, tools)`, `form.build(fields)`, `form.free(fields)` (each `(key, line, value)`) and `scrub.detect(value, m)` come in as arguments. A refusal names a line and a kind, never a match. Kinds: `form` (the bytes do not read back, or do not write again to the same bytes), `size` (over the ceiling), `tool` (the marker's tool is not in `public["tools"]`), and each kind `detect` returns for a free value, on its line. The repo is `public["tools"][tool]` alone.
- R3, the account. `accounts(env)` reads `gh auth status --json hosts`, never a token. `account(env, as_login)`: one account on github.com is that one; more than one needs `as_login`, the active one, else a refusal carrying `gh auth switch --user LOGIN`. `GH_TOKEN` or `GITHUB_TOKEN` in `env`, no `gh` on PATH, or no account: R7's road, the reason said. The repo goes as `github.com/OWNER/REPO`. Nothing switches an account.
- R4, the search. `search(env, repo, fingerprint)` runs `gh issue list -R REPO -S '<fingerprint> in:body' -s all --json number,title,state,url -L 5`: `none`, `open`, `closed` or `failed`, with what it found. Only the fingerprint leaves. A failed search is a line on the screen, never a refusal.
- R5, the one door. `approve(data, repo, login, notes, env, t) -> approved` and `_file(approved, repo, env) -> url` are the only functions that lead to a writing `gh` call; `_file` takes only what `approve` returns, the bytes and their SHA-256, and checks it again. `approve` refuses, exit 2, each with its own message: `/dev/tty` does not open; `CLAUDECODE` is in `env`; a process named `claude` is an ancestor, by one `ps` from PATH. The prefix `CLAUDE_CODE_` is not tested. It writes to the device alone: a head line, the bytes exactly, an end line, the repo, the login and that it shows on the issue, the notes. Added lines come from the catalogue by `t.text`; with colour off nothing is added. Taller than the terminal (a line's height is its width over the columns, a wide character two): a screenful, Enter on the device, on in the file's order. One line is read from the device, never stdin: only `send` passes; anything else, an end of input or an interrupt keeps the draft and returns no approval. `_file` runs the create verb with `-R github.com/OWNER/REPO -t <the first line> -F -`, the bytes after the second line on stdin, under a 60 s wall, and returns the URL.
- R6, no way round: no `--yes`, environment variable or config key stands in for the typed word, and no test hook does. A dry run is the caller's: `approve` without `_file`.
- R7, the browser's road. `web(data, repo, fingerprint)`, after the same check, screen and word: the search link and the new-issue link, prefilled when the link is under 6,000 bytes, bare otherwise, percent-encoded by the module's own function. It opens nothing.
- R8, the messages: ids under `issue.screen.`, `issue.send.`, `err.issue.send.`, in a new last section `## Issue`; nothing above it.
- R9, the tests: a temp HOME; PATH a stub folder, `/usr/bin`, `/bin`; a stub `gh` records argv and stdin and answers `auth status`, `issue list` and the create verb from a fixture; a stub `ps` prints a tree with no `claude`. The word is typed through `pty.fork`. `form` and `scrub` are fakes.
- R10, not this row's: `cli.py`, `.hygiene-allow`, `README.md`, `plugin.json`, any other module or test file.

## 3. Acceptance

Measured at 23330e2 in a Claude Code Bash call: no stream is a terminal, `/dev/tty` does not open (errno 6), `CLAUDECODE` is set and a `claude` process is an ancestor; a child of `pty.fork` opens `/dev/tty` and reads a typed word, once the parent keeps reading the master until the child's exit. A 4,107-byte draft written whole to an 80x24 pane shows no title above the prompt (the design's §2 item 10). `send.py` does not exist; `grep -rc 'issue create'` over the package counts 0.

| # | line |
|---|---|
| 1 | in a pty, `send` typed: the stub records one create; its `-R` is `github.com/<owner>/<repo>`; its `-t`, two line breaks and its stdin, joined, equal the bytes shown between the head and end lines, and the file |
| 2 | `y`, `yes`, `SEND`, an empty line, the device closed, an interrupt: no create recorded, no approval |
| 3 | `send` on stdin with no terminal: exit 2's refusal, nothing recorded |
| 4 | `CLAUDECODE=1` with a terminal: refused; a stub `ps` putting `claude` above: refused; `CLAUDE_CODE_USE_BEDROCK=1` alone: not refused |
| 5 | two accounts, no `as_login`: refused, holding `gh auth switch --user`; `as_login` not the active one: refused; `GH_TOKEN` set: R7's road and one line why |
| 6 | `check` with a fake `detect` giving `path` for one value: `[(its line, "path")]`; a `parse` that raises: `form`; over the ceiling: `size`; a tool outside the table: `tool`; no refusal holds a byte of the value |
| 7 | 44 lines, 4,107 bytes in a pty of 80x24: Enter asked between screens, the lines shown joined in order equal the bytes; at 200x60 no Enter asked |
| 8 | the file changed after `approve`: `_file` files the approved bytes; the approved bytes changed in memory: `_file` raises, nothing recorded |
| 9 | an open match: `open` with its URL; a closed one: `closed`; a list that exits 1: `failed`, and the screen shows one line for it |
| 10 | `web`: a 1 KB body gives a link with `title=` and `body=` under 6,000 bytes; 4,096 bytes of three-byte characters a bare link; no stub call |
| 11 | `grep -rc 'issue create'` over the package counts 1, in `send.py`; a test holds it |
| 12 | `make voice`, then `make check`, each once through the gate queue, green |

## 4. Not built

The drafts folder, `sent.json`, the refusal of a second send, `--not-a-duplicate`, `--as`, `--web`, `--dry-run` as flags, and every line `new` prints: the join's (rp6). The guard rule in the other plugin (rp7). Design/22 §6 question 2 is the owner's; this builds its recommended answer.

## 5. The landing

`plugin.json` stays as it is; the join takes the version. Phase 2 merges main after `rp1-shapes` lands, on the coordinator's word.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, a relay ledger. The report: head sha, the gate's ids and exits, acceptance 1 to 12 at the pin and now.

## 7. The fix of review 2

The coordinator's ruling of 2026-11-13 on review 2, at `3bbcce2`: a small fix, each part behind a test seen red there. R1-F1, R1-F4 and R1-F5 held and stay as they are.

- R2-F1, review 1's R1-F2 not yet met. A line written every 0.35 s or slower never reached the 3 s bound, so a blind stream answered each question. Now the answer to a question is refused, exit 2, nothing filed, whenever the wait after that question is drawn drops any byte: `err.issue.send.early`, one line that says input came before the question could be read and to run it again. The bound goes; a byte right after the word stays `err.issue.send.flood`.
- What this cannot tell apart: a writer that waits for each question to show and then answers is a person to this verb, since the screen is all it can watch. Refusing a session's own call is the guard's, another row (rp7).
- R2-F2, R1-F3's ruling unmet on a narrow or short screen. The page's question counts its own rows against the page, and the cursor's row too: a page holds `rows - 1 - h` rows of the draft, `h` the tallest of the three questions at that width. The size is read again at each page. A terminal with no room for one row of the draft beside the question, or for a fixed line of the screen, is refused, exit 2, before anything of the draft is drawn: `err.issue.send.small`.
- To `NICE_TO_HAVE.md` as rows, not built: review 2's R2-F3 (the line-11 walk misses an alias of `subprocess.Popen` and a bytes argv), the blank characters outside item 4(e)'s list that still pass, the `nfkc` kind against a form's own fixed lines, and an approval made by a direct call in the same process.

| # | line |
|---|---|
| 13 | a `send` line every 0.35, 0.5 and 1.0 s from before the screen, on a short draft and on one paged across several screens, and a 5 ms flood that stops at 2.6 s followed by one `send` at 3.3 s: each `err.issue.send.early`, exit 2, no create; a person's `send` written well after the question shows and the input is quiet: approved, one create |
| 14 | at 20x10, and after a resize from 80x24 to 80x10 at the first question, no page writes more rows than the screen has before a key is asked; at 80x1, 80x2, 1x12 and 2x12 `err.issue.send.small`, exit 2, before the head line is drawn |
