# Packet fh9-hour: `docs/first-hour.md`, two short tasks a newcomer can do right after setup

| item | value |
|---|---|
| from | agentik-hq's brief fh9-hour of 2026-11-14, R1 to R5; level S3, tier words |
| pin | agentik-commons main 43e902e (suite 0.7.2); worktree `.claude/worktrees/fh9-hour`, branch `fh9-hour`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; made-up names; no version set; no `install-cli` or `setup` on the real home |
| may touch | `docs/first-hour.md` (new); `.hygiene-allow` (two lines); this packet |
| verify | `make check` once, through the gate queue, `--strict` |
| acceptance | 1 to 7 below; verify green |
| budget | the packet first, then the page and the allow file together, by explicit path; about 40 tool calls |

## 1. The owner's words

"How close are we to being able to install this on my work computer?" He will install the suite on a second computer from the public repos alone, and strangers will after him. After `setup` and `claude`, nothing says what to try.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds.

- R1, the page: `docs/first-hour.md` is new, about 50 lines. A words helper reads it as an editor: a sentence that is not plain English is mended and recorded; no line inside a fence, no code span, no link target and no fact changes.
- R2, true on the day: the page names two tasks and adds no third. It says nothing of `agentik remove`, a starter profile or `agentik setup relay`.
- R3, the allow file: `.hygiene-allow` gains a comment, `# the first hour's page names the tools a newcomer types`, and a row, `docs/first-hour.md: sibling`. Nothing else is excused.
- R4, commits by explicit path: this packet first, then the page and `.hygiene-allow` together.
- R5, the check: `make check` through the gate queue, once, after the commits.
- Not this row's: `README.md`, `GUIDE.md`, anything under `plugins/`, `scripts/` or `tests/`; the organisation's page.

## 3. Acceptance

The page's command lines are pasted in a temp HOME under `env -i` with `PATH=/usr/bin:/bin`, by a script file that begins `set -eu` and `cd "$T" || exit 1`. The two tools' launchers are placed by each sibling checkout's own `install-cli --prefix "$T/.local"` from its main, read only, and `$T/.local/bin` goes first on PATH. At the pin the page does not exist, so line 1 and 2 fail; lines 3 to 6 were measured on 2026-11-13 with the decisions tool at 0.22.3 and the session tool at 2.0.0-alpha.107.

| # | line |
|---|---|
| 1 | `docs/first-hour.md` holds exactly two `## ` headings that start with a digit; `grep -ci 'night\|morning\|packet' docs/first-hour.md` prints 0 |
| 2 | every fenced line of the page is one of the five lines of the owner's brief, byte for byte |
| 3 | the scratch line, pasted as `mkdir` and `git -C <folder> init`: a folder `agentik-try` that is a git repo, exit 0 |
| 4 | in it, `agentik decisions init`: exit 0; its output names `.claude/edit-gates` and `/decisions:instruct`; `DECISIONS.md` and `CLAUDE.md` exist |
| 5 | the `new` line, then the `answer` line, each pasted whole: exit 0 each; the second prints ``answer: 1, Spaces; entry 1 under `### Every session` in DECISIONS.md`` and a line holding `+65 B`; `CLAUDE.md` holds `This repo indents with four spaces.` |
| 6 | `agentik session report` in that HOME, no session ever run: prints `the ledger is empty`, exits 2 |
| 7 | `scripts/hygiene --require-private --commits main..HEAD` ends `hits outside allowlist: 0`; `make check` green through the gate queue |

Where a line of 4 to 6 prints other words than the page quotes, no command changes: the record says so and the commit waits. Not pasted, since each needs a model and none is started: the line above the prompt, `/session:status`, `/agents:status`, a new session's answer, the refusal of a hand edit.

## 4. Not built

A third task; a session wrapping up at its checkpoint (it comes with the starter profile's row); the organisation's page linking this one; `agentik remove`.
