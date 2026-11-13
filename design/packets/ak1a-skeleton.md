# Packet ak1a: the `agentik` command's skeleton in the `suite` plugin

| item | value |
|---|---|
| from | agentik-hq's brief ak1a of 2026-11-12 (`history/sessions/BRIEF-2026-11-12-commons-ak1a-skeleton.md`), R1 to R9; level S3 |
| pin | agentik-commons main 6344a9e; worktree `.claude/worktrees/ak1a-skeleton`, branch `ak1a-skeleton` |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no `relay`/`agentik relay` `run`, `plan`, `gate`, `stop`, `kill`, `clean`, `resume`, nothing under `~/.local/state/agent-relay`; no `claude` process; no ledger edited; fixtures use made-up names |
| may touch | `plugins/suite/**`; `tests/test_agentik_suite.py`; `tests/test_voice.py`; `scripts/voice`; `design/voice/budgets.yaml`; `design/voice/checked.sha256`; `Makefile`; `.hygiene-allow`; `GUIDE.md` (§2's sentence on `suite`); `README.md`; `.claude-plugin/marketplace.json` (suite's `description`); `scripts/marketplace-check` (its comment); this packet; `history/sittings/2026-11-12-2.md` |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id> --strict` |
| acceptance | 1 to 8 below, each in a temp HOME, `env` exactly `HOME`, `PATH=/usr/bin:/bin` plus a folder of stubs, `XDG_CACHE_HOME`; `python3 -m unittest tests.test_agentik_suite` OK; verify green |
| budget | a commit per ruling group by explicit path, the packet first, the version bump last; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"I agree having a rich agentik command tool would be very useful. Make it a high quality modern CLI tool that is dynamic and has high quality concise human friendly feedback (using respeak to help with the voice). Make plugin configuration discoverable and drill down."

## 2. Rulings

- R1, the layout. `plugins/suite/` gains `bin/agentik-suite` (a copy of `scripts/plugin-launcher`), `lib/agentik-tool.conf` (`tool_name=agentik-suite`, `remedy=agentik-commons/setup`, `runner=agentik-suite`, `old_name=`, `old_state=`), `lib/agentik-suite` (the four-line runner), `lib/agentik_install.py` (a copy) and the package `lib/agentik_suite/`. A test holds each copy byte-equal to its canonical file. The door is not copied in and not changed.
- R2, the floor. Standard library only, Python 3.9, run by the launcher under `/usr/bin/python3 -I`. No tool's name is compiled into the package, its messages or its tests; a file that must name a sibling gets its `.hygiene-allow` row with its reason.
- R3, `term`, the one writer. Every byte a person reads goes through it, by message id; a test fails on a `print` or a stream write elsewhere in the package. Per stream, by `isatty` alone: on a terminal, colour, the glyphs `✓ ! ✗ ·`, the last column cut with `…` at the terminal's width; off a terminal the words `ok`, `warn`, `FAIL`, `note`, no escape byte, no cut value, no redraw. `NO_COLOR` set, `TERM=dumb` or `--no-color` turns colour off. Left-aligned columns, two spaces between, bold for a name, dim for a path or hint; no box, banner or border. Nothing is told by colour alone.
- R4, the catalogue. `lib/agentik_suite/messages.md`: one list item per message, `` - `id`: text ``, placeholders `` `{name}` ``. The loader takes the backticks off a span that is exactly one placeholder and keeps every other span. The voice: the result first, then the fact, then the next command; subject first; no "successfully", "please" or "oops", no exclamation mark; an error says what failed, why, and the one command that mends or shows more; a name as the user would type it; a number keeps its unit.
- R5, the voice gate. `make voice` runs the respeak scanner `respeak-measure.py <catalogue> --config design/voice/budgets.yaml --fail-on warn` (max 20, avg 12 words a sentence), found by `RESPEAK_ROOT`, else the newest copy in Claude Code's plugin cache, never a sibling path; with neither it exits 2 and writes nothing. On exit 0 it writes `design/voice/checked.sha256`, one `shasum -a 256` line. `make check` gains a stdlib step, red when the catalogue differs from that line; `make voice` is not in `make check`.
- R6, the verbs. Bare, `help`, `-h`, `--help`: the verbs with a line each, then each `agentik-*` executable on PATH by name and path, first in PATH order winning, then one `next:` hint. `--version`, `version`: `agentik-suite <version>` from the manifest. An unknown word: the nearest known one (`difflib`), exit 2. `setup` without `--dry-run`: exit 2, one line saying this version only plans.
- R7, `setup --dry-run [PLUGIN...]`, a plan that writes nothing; with no name, the manifest's `dependencies`. Seven numbered steps, each a read with a state (`ok`, or what setup would do and the exact command): (1) `claude`, `git`, a Python at the floor; (2) the `agentik` marketplace in `known_marketplaces.json`; (3) each plugin in `installed_plugins.json` (`plugins["<name>@agentik"][0].version`, `.installPath`), both under `${CLAUDE_CONFIG_DIR:-~/.claude}/plugins/`, absent reading "not known"; (4) each `~/.local/bin/agentik-<name>` with `VERSION=` equal to the plugin's; (5) the suite's own launcher and the door; (6) `~/.local/bin` on PATH, else the line to add; (7) the doctors it would run. `claude` is looked up, never run. Exit 0.
- R8, the rules every verb holds (quoted whole):
  - Grammar: `agentik <verb> [<noun>...] [flags]`; a verb is one lowercase word; a flag is never a verb.
  - Streams: stdout carries the answer and nothing else; stderr carries progress, notes, hints and errors. A verb prompts only when stdin and stderr are terminals; off a terminal a missing answer is exit 2 with the flag that gives it.
  - `--json`: every read takes it and prints one object, `{"schema": "agentik.<verb>/<n>", "ok": true, ...}`; on failure `{"ok": false, "error": {"code", "message", "remedy"}}`, still on stdout, still with the exit code. A new key does not raise `<n>`.
  - Exit codes: 0 done; 1 a check said no; 2 usage or a failed precondition; 3 not installed. They report the task, not the content.
  - Flags: `--json`, `-q/--quiet` (no hints, no progress), `--no-color`, `-h/--help`; a verb that writes also takes `--dry-run` and `-y/--yes`.
  - A read starts no model, never loops, and writes nothing outside `${XDG_CACHE_HOME:-~/.cache}/agentik/`, where the launcher keeps Python's bytecode.
- R9, the records. GUIDE §2's sentence on `suite`, the manifest's and the marketplace entry's `description`, the Makefile's head comment and the README stop saying "manifest-only" or "no code": `suite` is the default set and the command that manages it. `scripts/marketplace-check`'s comment follows. The README gains the verbs as built.
- Decided: `--json` on `help`, `version` and `setup --dry-run` (`steps: [{n, id, state, detail, command}]`); no cache; no `install-cli` verb.

## 3. Acceptance

At 6344a9e every line is `env: plugins/suite/bin/agentik-suite: No such file or directory`, exit 127 (measured).

| # | line |
|---|---|
| 1 | `plugins/suite/bin/agentik-suite --version` prints `agentik-suite 0.2.0`, exit 0 |
| 2 | `setup --dry-run`: seven steps, exit 0; the temp HOME's files and hashes outside `$XDG_CACHE_HOME/agentik/` the same before and after; a stub `claude` that records its calls records none |
| 3 | with the two plugin files written, steps 2 to 4 read `ok` for what is there and name the command for what is not; both absent, every plugin reads "not installed", exit 0 |
| 4 | piped, `help` and `setup --dry-run` hold no escape byte and the words `ok` and `note`; under a pty, colour and a glyph; under a pty with `NO_COLOR=1`, no colour |
| 5 | `setup --dry-run --json` and `version --json` each print one JSON object with `schema` and `ok`, nothing else on stdout |
| 6 | `agentik-suite stup` exits 2 naming `setup`; `agentik-suite setup` exits 2 and writes nothing |
| 7 | a catalogue changed by one word turns `make check` red until `make voice` runs again; a `print(` added to the package turns R3's test red |
| 8 | the two copies byte-equal to `scripts/plugin-launcher` and `scripts/agentik_install.py`, the conf's five keys; `make check` green, hygiene included |

## 4. Not built

`config`, `describe`; the door 0.2.0 or any change to `bin/agentik`; `install-cli`, a root `setup` file, any write outside the cache folder; any `claude plugin` call; `doctor`, `status`, `remove`, `update`, `init`; a skill or command file in the plugin.

## 5. The landing

Version: `plugins/suite/.claude-plugin/plugin.json` to `0.2.0` in the last commit that touches `plugins/suite/`. `scripts/plugin-version-check` reads `plugin/` only, so nothing checks this bump.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list. The report: head sha, gate id and line, acceptance 1 to 8 at the pin and now.

## 7. Fix round 1 (review 1)

| item | value |
|---|---|
| from | agentik-hq's fix brief of 2026-11-13 for ak1a, R1 to R13; the review's seven findings, its leads L1 to L9 |
| pin | `ak1a-skeleton` at 3b7cc56; the branch continues, no new one |
| may touch | as above, and `NICE_TO_HAVE.md`, `history/sittings/2026-11-13-2.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |

The findings, as this round reads them:

- F1: one commit's Makefile comment trips the commit-range hygiene scan; mended by the replay of phase 2, not here.
- F2: with every launcher placed and the door absent, the door's row points at a step that prints nothing.
- F3: the closing hint never says done, and sends the reader to lines that cannot work yet.
- F4: a plugin whose files are gone reads installed, and a printed path with a space splits in two.
- F5: a closed stdout or stderr, or a reader that has gone, gives a traceback and the wrong exit.
- F6: a character the stream cannot encode, the cut mark or a stray byte in an argument, gives a traceback.
- F7: a crafted file of Claude Code's gives a traceback, or puts an escape byte into piped output.

Rulings:

- R1: the door's row names one placed launcher's `install-cli` when a launcher is placed and step 4 prints none; else it says step 4's first `install-cli` places it.
- R2: done is judged on steps 1 to 6; step 1 blocked names what to install and withholds every `run:` line; else the hint sends the reader to the `run:` lines in order; a doctor's line shows only once its launcher is placed.
- R3: step 3 reads `ok` only when the entry's `installPath` holds the plugin's launcher; every path in a command is `shlex.quote`d.
- R4: `term` drops output to a closed or broken stream, at a write and at exit, with no traceback; the exit code is the verb's.
- R5: the glyph probe covers every non-ASCII character `term` prints; what a stream cannot encode is replaced; `--json` is ASCII-safe.
- R6: any failure to parse a file reads as not known; control characters (C0, DEL, C1) from a file or the environment never reach the output.
- R7 (amends R3 above): on a terminal nothing is cut; a last cell too wide moves whole to the dim line under its row. No place to cut is left, so the cut mark is gone.
- R8: a list item the loader cannot read is a `ValueError`, and the catalogue's test is red on it.
- R9: a missing catalogue, or a manifest unread where the version is asked, is one plain line naming the file, exit 2.
- R10: the voice pass's catalogue, proved by respeak's `respeak-verify-edit.py`, then this round's messages in its voice, `setup.suite.unread` among them; `make voice` and its sidecar.
- R11: NICE rows for L4, L5, L6, L8, the rest of L7, and the note that a to-do row reads as information.
- R12: `scripts/hygiene --commits 3b7cc56..HEAD` reads 0 hits outside the allowlist.
- R13: each ruling's test red at 3b7cc56 first; commits by ruling group.

Acceptance (each a test in `tests/test_agentik_suite.py`; at 3b7cc56 each is as the review saw it):

| # | line | at 3b7cc56 |
|---|---|---|
| 1 | every launcher placed, the door absent: the door's row names an `install-cli` whose file exists | the row names none |
| 2 | steps 1 to 6 `ok` give the done hint; no `claude` gives a hint naming `claude` and no `claude plugin` line; on a fresh home each `run:` line, run in order against stubs, exits 0, and no doctor line comes before its launcher | "run each line" always; doctors on a fresh home |
| 3 | an `installPath` gone reads not whole and prints no missing path; a path with a space is one shell word | `ok`, and the path split |
| 4 | `--version >&-` exits 0, `stup 2>&-` 2, `help` to a gone reader 0, stderr empty | exit 1, 1, 120 |
| 5 | a pty with `LANG=en_US.ISO8859-1`: `setup --dry-run` exits 0; `$'\xff' --json`: one object from ASCII bytes, exit 2 | `UnicodeEncodeError`, exit 1 |
| 6 | 100,000 `[` exits 0 with the plugins not known, `--json` too; ESC in a version leaves no escape byte piped | `RecursionError`; an escape byte |
| 7 | a pty 80 and 40 columns wide, fresh home: no `…`, every `run:` line whole | 12 of 16 rows cut at 80 |
| 8 | a catalogue copy with a capital in an id turns its test red | skipped, green |
| 9 | the first eight lines hold; tests changed only where words changed | 25 tests OK |
| 10 | `make voice` exit 0; the gate's `make check` exit 0; R12's scan 0 hits | not run |
