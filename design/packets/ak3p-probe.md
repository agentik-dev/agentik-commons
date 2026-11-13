# Packet ak3p: `scripts/setup-probe`, then the join of the four branches and the proof end to end

| item | value |
|---|---|
| from | agentik-hq's brief ak3p of 2026-11-13, R1 to R5 and J1 to J5; hq design/15's row ak3 (§9); level S3 |
| pin | agentik-commons main d795d4a (`Merge su1-status-check`, suite 0.5.0); worktree `.claude/worktrees/ak3p-probe`, branch `ak3p-probe`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, install or sync; the merges of J1 the only merges; no bare `make`; no relay verb or binary; no `claude` process but the probe's own, in its temp HOME; made-up names in fixtures |
| may touch | first build: `scripts/setup-probe`; `tests/test_setup_probe.py`; this packet; `history/sittings/2026-11-13-11.md`. The join, besides what the merges bring: `README.md`; `NICE_TO_HAVE.md`; `plugins/suite/.claude-plugin/plugin.json`; `plugins/suite/lib/agentik_suite/cli.py`; `plugins/suite/lib/agentik_suite/messages.md`; `tests/test_agentik_suite.py`; `design/voice/checked.sha256`; a file that holds a probe's fault, with its test |
| verify | first build: `make check` once through the gate queue, `--strict`; the join: `make voice`, then `make check`, each once through the gate queue, `--strict` |
| acceptance | 1 to 6 below; `python3 -m unittest tests.test_setup_probe` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first, the version bump last; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"I want to use it today." Three builders work beside this one from the same pin: `ak2b-reach` (the suite's `install-cli`, the root `setup`, `make install`), `ak3-setup` (`setup` applied) and `ak3d-doctor` (`doctor`). The first build writes the probe against what their briefs promise. The second part, on the coordinator's word, joins the branches and runs it.

## 2. Rulings

The repo keeps no `DECISIONS.md` and no `CLAUDE.md`; `GUIDE.md` binds. Cited: hq entry 6 (the standard library alone), hq entry 37 (made-up names).

- R1, the files: `scripts/setup-probe` and `tests/test_setup_probe.py`, the packet and the charter. No other file before the join.
- R2, the script: `setup-probe [--keep] [--code DIR] [--claude PATH]`, in `suite-probe`'s shape and with its lines (`ok`, `FAIL`, `note`; last `setup-probe: go` or `setup-probe: stop: <n> failed`; exit 0, 1, or 2 for usage or a missing prerequisite). Run by hand, never by `make check`; no model is reached. Under a fresh temp dir T it clones this checkout's HEAD and, at main, each checkout `DIR/agentik-<name>` the suite's manifest names as a dependency, and writes `T/market` as `suite-probe` does. Every command runs as `env -i HOME=T/home PATH=/usr/bin:/bin:<a folder holding only claude> DISABLE_AUTOUPDATER=1 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, under the sandbox that denies outbound IP. Nothing outside T is written; T is removed unless `--keep`.
- R3, its steps. (1) `claude plugin marketplace add T/market`, by the probe: the published marketplace is a network read, so the local one stands in and setup's step 2 reads ok; a `note` says so. (2) A listing of every path under `T/home`, then `<the commons clone>/setup --yes --json`; `ok`: exit 0, and `ran` holds one `claude plugin install <name>@agentik` for each dependency, one `install-cli` for each dependency whose plugin ships a launcher, and the suite's own `install-cli`. (3) Every path under `T/home` new since the listing is in `wrote`, or under a path in it, or Claude Code's own (`T/home/.claude.json`, anything under `T/home/.claude/`), or bytecode under `T/home/.cache/agentik/`; any other is a `FAIL` naming the first five. (4) Each file hashed, then `setup --yes --json` again: exit 0, `nothing` true, `ran` empty, and no file outside `T/home/.cache/agentik/` new, gone or changed. (5) With `T/home/.local/bin` first on PATH: `agentik --version` prints `agentik 0.2.0`; `agentik setup --dry-run --json` reads every row of steps 1 to 6 `ok`; `agentik doctor --json` is one object whose first group, the suite's, holds no `fail`. A `fail` in another tool's group is a `note` with its detail, never a `FAIL`: a tool's own doctor may fail outside a session.
- R4, the JSON it reads. `setup --json`: `ok`, `ran: [{n, command, exit}]`, `wrote` (absolute paths), `nothing`, `steps: [{n, id, state, subject, detail, command}]`. `doctor --json`: `failed`, `tools: [{name, checks: [{name, status, detail, remedy}]}]`.
- R5, the test: `suite-probe`'s three for this script (its shape; `--help` prints the usage line, exit 0, and a bad flag exits 2 with nothing on stdout; no Makefile line names it), and its rules for a new path and for `ran` over made-up reports, no process started.
- J1 to J5, the join, on the coordinator's word: the merges of `ak2b-reach`, `ak3-setup`, `ak3d-doctor` in that order, one commit each; the clashes kept both sides (`cli.py`'s imports, `VERBS`, `WRITES`, `VALUE_FLAGS` as the brief writes them, and its docstring for the three verbs); the README's table and opening; NICE rows n31, n39, n46, n47 leave once their tests are seen; `plugin.json` to `0.6.0` alone in the last commit that touches `plugins/suite/`; then `make voice`, `make check` and the probe once by hand. A probe's `FAIL` is mended in the file that holds it, with a test, in its own commit.

## 3. Acceptance

Measured at d795d4a: there is no `scripts/setup-probe`; `setup --yes` prints `Setup needs --dry-run`, exit 2; `doctor` is not a verb, exit 2; there is no root `setup`. With the real `claude` 2.1.323 in a temp HOME over local clones, `marketplace add` and three `install`s wrote only `.claude.json` and files under `.claude/`; each plugin's `install-cli` then wrote its launcher, its old names' links, a door at `VERSION=0.1.0` and a tree under `.local/share/agentik-<name>/`.

| # | line |
|---|---|
| 1 | first build: `python3 -m unittest tests.test_setup_probe` OK; `scripts/setup-probe --help` prints its usage, exit 0; `--bogus` exits 2 |
| 2 | first build: `make check` once through the gate queue, green |
| 3 | the join: the three merges made, `git status` clean, each of J2's lines as written |
| 4 | the join: `make voice`, then `make check`, green, on the head that holds `0.6.0` |
| 5 | the join: `scripts/setup-probe` ends `setup-probe: go`, exit 0 |
| 6 | the join: the owner's two sets of lines, each run first in a temp HOME |

## 4. Not built

GUIDE §11, `remove`, `update`, `init`: later rows. Any install on any machine: the probe's temp HOME is the only home written.

## 5. The landing

The coordinator lands this one branch, which then holds all four rows. `plugin.json` to `0.6.0` at the join; nothing checks this bump. The coordinator owes one respeak pass over the joined catalogue before the landing; if it changes a message, `make voice` and `make check` again.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real HOME's Claude Code files. The probe's lines name other checkouts, so they stay out of this packet, the charter and every commit. The report: head sha, gate ids and exits, acceptance 1 to 6 at the pin and now.
