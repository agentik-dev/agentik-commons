# Packet ak2b: the suite's command reaches the terminal: `install-cli`, the root `setup`, `make install`

| item | value |
|---|---|
| from | agentik-hq's brief ak2b-reach of 2026-11-13, R1 to R9; hq design/15's row ak2, its second part (§3 items 1 and 4, §7.1 step 5, §9); level S3 |
| pin | agentik-commons main d795d4a (suite 0.5.0); worktree `.claude/worktrees/ak2b-reach`, branch `ak2b-reach`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`, never `make install`; no relay verb or binary; no `claude` process; every run in a temp HOME; made-up names |
| may touch | `scripts/agentik_install.py`; `plugins/suite/lib/agentik_install.py`; `plugins/suite/lib/agentik_suite/install.py`; `plugins/suite/lib/agentik_suite/plan.py`; `plugins/suite/lib/agentik_suite/cli.py` (R4's lines alone); `plugins/suite/lib/agentik_suite/messages.md` (R8's lines alone); `setup`; `Makefile`; `tests/test_ak2b_reach.py`; `tests/test_agentik_suite.py` (`PlanTruthTest` alone); `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-13-8.md` |
| verify | `make voice`, then `make check`, each once, through the gate queue, `--strict` |
| acceptance | 1 to 9 below; `python3 -m unittest tests.test_ak2b_reach` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

## 1. The owner's words

"I want to use it today." Three builders work beside this one from the same pin (`setup` applied, `doctor`, a probe), and a join merges the four branches: this row touches only the files named here, and in a shared file only the lines named.

## 2. Rulings

The repo keeps no `DECISIONS.md` and no `CLAUDE.md`; `GUIDE.md` binds. Cited: hq entry 6 (`/usr/bin/python3`, a 3.9 floor, the standard library alone), hq entry 37 (made-up names in fixtures and this packet).

- R1, what stands. The packets ak1a, ak1b, ak2-door and su1 bind this row: the floor, `term` the one writer, the catalogue and its voice (the result, the fact, the next command), the streams, the `--json` object, the four exits, no tool's name in the package or its tests. New tests go in `tests/test_ak2b_reach.py`.
- R2, the module, `scripts/agentik_install.py`, then `cp` to `plugins/suite/lib/agentik_install.py` (`LayoutTest` holds them equal). No tool's vendored copy moves here.
  - `door_fate(path, door)` returns `write` (no file there, or an older door), `keep` (equal or newer), `link` (a symlink) or `unversioned` (not a regular file, or a `VERSION` line here or there that reads as no version). It opens a regular file only, decided by `lstat`, and never raises.
  - `_door` acts on that fate. The line it returns is ASCII: a byte outside ASCII is shown escaped.
  - `install(prefix=None, env=None, dry_run=False)` returns what it returns today plus `door_fate`, read before any write, and `on_path`: true when `<prefix>/bin` is an entry of `env["PATH"]`, compared by `normpath`. With `dry_run` it takes no lock and writes nothing; `tree` is None and `pruned` is empty.
  - `install_cli` prints one more line when `on_path` is false: `<prefix>/bin is not on PATH; add: export PATH="<prefix>/bin:$PATH"`.
- R3, the verb: `install-cli [--prefix P]`, a write, so it takes `--dry-run` and `-y`. A new module `plugins/suite/lib/agentik_suite/install.py` holds `do_install_cli(cmd, nouns)`. It calls `agentik_install.install`, never `install_cli`, and prints from the catalogue: the result on stdout in one line (the launcher, its version, the tree), the door's fate when it is not `write`, each `pruned` line, and on stderr one hint with the `export PATH` line when `on_path` is false. `--json`: `schema` `agentik.install-cli/1`, `ok`, `launcher`, `tree`, `version`, `door`, `door_fate`, `on_path`, `dry_run`. An `OSError`, `KeyError` or `ValueError` from `install` is exit 1 with one line. `--prefix` joins `VALUE_FLAGS`; a word after the verb is exit 2.
- R4, `cli.py`, these lines and no other: `install-cli` appended to `VERBS` and `WRITES`; `"--prefix": ("prefix", "install-cli")` in `VALUE_FLAGS`; `install` added to the package import; a method `do_install_cli` directly under `do_version`; and the dash. A catalogue id holds no dash, so a verb's ids and its method are found with the dash as `_` (`verb.install_cli`, `usage.install_cli`, `do_install_cli`). The module's docstring is left to the join.
- R5, `plan.py`.
  - `manifest(lib)` reads `lib/plugin.json` where `agentik_install.is_frozen(lib)`, so the installed command plans the default set.
  - The path a row names for this command is `<plugin>/bin/<tool>` in a plugin and `<lib>/<runner>` in a frozen tree, the runner's name from the conf.
  - Step 5's `suite` row, when it is not ok, carries the command `<that path> install-cli`, as `run`. Its three messages say setup would place it.
  - Step 5's `door` row reads `door_fate` against this command's own door: `keep`, `link` and `unversioned` are ok, each with its own detail; `write` is todo, with the same command, or with none and "the line above places it" when the `suite` row already carries it. A plugin's launcher is never the door's command.
  - `_closing` in `cli.py` needs no change. `PlanTruthTest`'s tests of the old step 5 are rewritten; no other test there moves.
- R6, the root `setup`: `sh`, executable, at most six lines. It execs `plugins/suite/bin/agentik-suite setup "$@"`, found from its own path whatever the cwd.
- R7, the `Makefile`: `install`, one recipe line, `plugins/suite/bin/agentik-suite install-cli`, with `--prefix "$(PREFIX)"` when `PREFIX` is set; `sh -n setup` in `lint`; the head comment and `help` say so.
- R8, the catalogue: the new ids go in a new section `## Install`, directly above `## Errors`; `verb.install_cli`, `usage.install_cli` and `flag.prefix` go at the end of their runs in `## Help`; the `setup.suite.*` and `setup.door.*` lines are reworded. No other line moves.
- R9, not this row's: `README.md`, `plugin.json`, `GUIDE.md`, `NICE_TO_HAVE.md`, `scripts/door-probe`, `tests/test_agentik_suite.py` outside `PlanTruthTest`.

## 3. Acceptance

Each in `Home`, the prefix a second temp folder. Measured at d795d4a: lines 1 to 3 print `install-cli is not a verb. Run agentik-suite --help for the list.`, exit 2; for line 4 the module's `install` over a FIFO at the door's path ran until a 5 s alarm killed it, and over a door reading `VERSION=0.2.\xff` under `LC_ALL=en_US.UTF-8` it ended in a `UnicodeEncodeError` traceback, exit 1; for line 5 the command frozen under a prefix printed `Setup plan for no plugin, since the manifest lists none` and named `<share>/agentik-suite/bin/agentik-suite`, a file that does not exist; for line 6 step 5 reads `not placed; a later version places it`, with no command, and a door at `VERSION=0.1.0` reads `in place`; there is no root `setup` and no `install` target.

| # | line |
|---|---|
| 1 | `install-cli --prefix P`: exit 0, one stdout line naming `P/bin/agentik-suite` and the version; `P/bin/agentik-suite --version` prints that version; `P/bin/agentik --version` prints `agentik 0.2.0`; HOME outside the cache is unchanged |
| 2 | `--json`: one object with R3's keys, `door_fate` `write`, `dry_run` false. `--dry-run --json`: `tree` null, `dry_run` true, and no `P` afterwards |
| 3 | `P/bin` off PATH: one stderr hint holding `export PATH="P/bin:$PATH"`; on PATH: none; `-q`: none. `install-cli extra` and `--prefix` with no value exit 2; `help` lists the verb |
| 4 | over each door at `P/bin/agentik`: a FIFO: back inside 5 s, exit 0, still a FIFO, fate `unversioned`; `VERSION=0.2.\xff` under `LC_ALL=en_US.UTF-8`: exit 0, no `Traceback`, the bytes kept; `VERSION=0.9.0`: the same byte for byte, `keep`; `VERSION=0.1.0`: now `0.2.0`; a link: left, `link` |
| 5 | `P/bin/agentik-suite setup --dry-run --json`: `plugins` is the manifest's `dependencies`; the first word of step 5's command is a file that exists, and `<that word> --version` exits 0 |
| 6 | empty HOME, a stub `claude`: step 5's `suite` row is todo with `<this launcher> install-cli`, its `door` row has no command; that command run with HOME set leaves both rows ok. With the suite's launcher at this version and a door at `VERSION=0.1.0`: the `door` row is todo and carries the command; after it the door reads `0.2.0` |
| 7 | from another cwd, `<root>/setup --dry-run` prints the plan, exit 0; `sh -n setup`; six lines at most |
| 8 | a test runs `make -n install PREFIX=/x`: one line, ending `install-cli --prefix "/x"`; without `PREFIX` it ends `install-cli` |
| 9 | `make voice`, then `make check`, each once through the gate queue, green |

## 4. Not built

`setup` applied, `doctor`, a probe (the rows beside this one). GUIDE §11, a tool's claimed top-level verb, `scripts/door-probe` gaining this checkout, `uninstall`: later rows. The README and the version: the join.

## 5. The landing

`plugin.json` stays at 0.5.0: the join takes 0.6.0, merging this branch first, then `ak3-setup`, then `ak3d-doctor`.

## 6. Forbidden reads and report

`~/.local/state`, transcripts, the private hygiene list, the real HOME. The report: head sha, gate ids and exits, acceptance 1 to 9 at the pin and now.
