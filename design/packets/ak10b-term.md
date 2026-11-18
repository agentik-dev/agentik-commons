# Packet ak10b-term: `scripts/sync` places the writer `term` and its catalogue in a tool

| item | value |
|---|---|
| from | agentik-hq's brief ak10b-term of 2026-11-17, R1 to R7; hq design 15's P7 (one writer module, `term`, draws everything; a tool's verb uses the copy `sync` places) and §5.3 (a tool's voice gate); level S3 |
| pin | agentik-commons main 2de3424 (suite 0.7.34); worktree `.claude/worktrees/ak10b-term`, branch `ak10b-term`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; `scripts/sync` runs only on temp trees, never on a real tool repo; nothing under `plugins/suite/` changes; made-up names in fixtures |
| may touch | `scripts/sync`, `tests/test_sync.py` (the plugin tests' placed set and closing line), `tests/test_ak10b_term.py` (new), `GUIDE.md` (§10), `README.md` (the `scripts/sync` row), `history/sittings/2026-11-17-3-ak10b-term.md`, this packet |
| verify | the two test files directly; `make check` once, last, through the gate queue |
| acceptance | 1 to 5 below |

## 1. The finding

hq design 15's P7: one writer module, `term`, draws everything a person reads, and a tool's top-level verb uses the copy `scripts/sync` places beside `agentik_install.py`. At the pin `term.py` (440 lines) and `catalogue.py` (39 lines) import the standard library alone, tied to the suite only by `from . import catalogue` and `catalogue.PATH`, the `messages.md` beside `catalogue.py`; `term.py` names one message id itself, `err.next`, in `Term.error`; `sync` has no line for `term`, and no tool repo holds one.

## 2. Rulings

- R1, the package: in a tool the writer is `plugin/lib/agentik_term/`, `term.py` and `catalogue.py` byte-equal to commons' files under `plugins/suite/lib/agentik_suite/`, and an `__init__.py` whose bytes `sync` fixes. A tool reads `from agentik_term import term`. Commons' two files do not change, and commons keeps one copy of each.
- R2, the catalogue: `plugin/lib/agentik_term/messages.md` is the tool's own, written once when absent, by a temp file and a rename: a title, one line saying whose file it is, and every id `term.py` names, each with commons' text. In no sum; a second sync leaves a changed one.
- R3, the lines: where the target has `plugin/lib/`, `sync` places R1's three files, lists them in `scripts/vendored.sha256`, and its closing line names them. A target with no `plugin/lib/` gets nothing new.
- R4, the seed is proved: a test reads `term.py` for each id it names and fails where the seed lacks one or holds another text than commons' `messages.md`.
- R5, the proof in a made-up tool, in a new Python process with only its `plugin/lib` on the path.
- R6, the guide: §10 says the package, its files, the catalogue written once, the import line, and that a tool takes its own voice gate (design 15 §5.3's `make voice` and its sidecar) in the row that first moves a verb onto `term`; the README's `sync` row gains the same in a line.
- R7, what stays: no tool repo is synced or changed; the relay and respeak (no `plugin/lib/`) take nothing; nothing under `plugins/suite/` changes, so the suite's version stays.

## 3. Interfaces

- `sync` reads the ids it seeds from its own list, `term_ids` (today `err.next`), and each one's line from commons' `plugins/suite/lib/agentik_suite/messages.md`, before anything is written: an id with no line there is exit 2, nothing written.
- The placed `__init__.py` is one docstring line, written by `sync` from its own text, mode 644, listed. `term.py` and `catalogue.py` are placed at 644 and listed.
- The seed: `# Messages`, a blank line, one line saying the file is the tool's own catalogue and not a vendored copy, a blank line, then one `- \`<id>\`: <text>` line per id, as commons' file has it. `catalogue.load` reads it as is.
- The closing line, with `plugin/lib/`: `sync: <target>/plugin: lib/agentik_install.py, lib/agentik_term/__init__.py, lib/agentik_term/term.py, lib/agentik_term/catalogue.py, bin/<tool>, bin/agentik`.

## 4. Acceptance

Each on a temp tree made by the test, a git checkout with `plugin/.claude-plugin/plugin.json` naming a made-up tool.

| # | line | at the pin |
|---|---|---|
| 1 | R5: sync a tree with `plugin/lib/`; in `/usr/bin/python3 -I` with that `plugin/lib` alone on `sys.path`, `from agentik_term import term`, a message added to the tool's `messages.md`, `Term.line` and `Term.error` with a next command read off a pipe as the plain form; `shasum -a 256 -c scripts/vendored.sha256` passes; a second sync restores a `term.py` changed by a byte and keeps the changed `messages.md` (`-k test_r5`) | red: no `plugin/lib/agentik_term/` is placed |
| 2 | R4: every id `term.py` names is in the seed with commons' text (`-k test_r4`); with `err.next` taken out of the seed by hand the same check is red | red: no seed |
| 3 | sync a tree with no `plugin/lib/`: `scripts/vendored.sha256` byte-equal to the pin's for the same tree (`-k test_r3`) | seven rows, sum 61746a92 at the pin |
| 4 | `cmp` of the placed `term.py` and `catalogue.py` against commons' files: equal; `git diff 2de3424 -- plugins/suite/` empty | no copy placed; diff empty |
| 5 | `scripts/hygiene --require-private --commits main..HEAD` exits 0; `make check` green through the gate on the head handed back | green |
