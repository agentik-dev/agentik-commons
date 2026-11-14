# agentik-commons

agentik-commons is the way in to agentik: one `setup` that installs the default plugins (session, decisions and agents) and the `agentik` command that manages them.
Use it when a machine has Claude Code and nothing of agentik's.

Both lines are typed in a terminal; `setup` shows its plan and asks once before it writes anything:

```sh
git clone https://github.com/agentik-dev/agentik-commons && agentik-commons/setup
claude
```

It needs Claude Code, git and the system's Python at 3.9 or newer, and it installs no package.
Part of [agentik](https://github.com/agentik-dev): what each plugin does, and how to leave.

## For maintainers

The shared ground of the five agentik tools (session, decisions, respeak, relay and agents): the `agentik` front door, the one `agentik` marketplace that lists the five plugins and `suite`, the consistency guide, and the canonical copies of the scripts each tool repo vendors.
The `suite` plugin also installs with Claude Code's own verbs and no clone; that route places no `agentik` command on the terminal, so a person's install is the clone above:

```sh
claude plugin marketplace add agentik-dev/agentik-commons && claude plugin install suite@agentik
```

`suite` is this repo's one plugin: the suite's default set, whose `dependencies` on session, decisions and agents Claude Code installs and enables with it, and the `agentik-suite` command that manages it (below). Updates stay `claude plugin marketplace update agentik && claude plugin update <name>@agentik`.

A clone and its `setup` set a machine up, the steps above included: `git clone https://github.com/agentik-dev/agentik-commons && agentik-commons/setup` runs `agentik-suite setup` from the clone, which adds the marketplace, installs each plugin, places each launcher, the suite's command and the `agentik` door in `~/.local/bin`, and prints the `export PATH` line when that folder is off PATH. `make install` puts the suite's command and the door on this terminal alone, under `PREFIX` when it is set.

## What it holds

| path | what |
|---|---|
| `bin/agentik` | the front door, POSIX `sh`: `agentik <tool> args…` execs `agentik-<tool>` from PATH, else hands the word to `agentik-suite`; bare `agentik` is the suite's help, or the list of tools when the suite is not on PATH; exit 3, one line, when neither is there |
| `.claude-plugin/marketplace.json` | the `agentik` marketplace as published: six `git-subdir` entries on `github.com/agentik-dev`, public repos only, the five tools' at `plugin` and `suite`'s on this repo's own url at `plugins/suite`, checked by `scripts/marketplace-check`; a plugin whose repo is not public reaches the owner's machine through the local file's overlay only |
| `plugins/suite` | the `suite` plugin: `plugin.json` and its `dependencies`, and the `agentik-suite` command, its launcher in `bin/` beside a copy of the front door, held byte-equal by a test, and its stdlib package in `lib/agentik_suite/`, whose every message is in `messages.md` |
| `GUIDE.md` | the conventions every tool repo follows: layout, naming, verbs, exit codes, README shape, install and hygiene |
| `docs/sibling.md` | the paragraph each README carries under "Conventions shared with the sibling plugins" |
| `scripts/hygiene` | the canonical hygiene scan, its `renamed` group included |
| `scripts/recordlint [FILE...]` | holds `HANDOFF.md` and `NICE_TO_HAVE.md` to their tables (GUIDE §9): one `path:line: rule: detail` line per finding, exit 2; a file without its header is skipped |
| `scripts/bounded` | the breaker `make check` runs under in each tool repo |
| `scripts/plugin-version-check` | run from a plugin repo's root: exit 1, one line per file, when `plugin/` changed after the commit that last changed `plugin.json`'s version, or the branch changed `plugin/` since a merge base with `main` (else `origin/main`; every base of a criss-cross) and its version is not above that base's (GUIDE §7) |
| `scripts/plugin-description-bytes [--max BYTES] [PLUGIN_DIR]` | a plugin's loaded description bytes, one line per command, skill and agent type, a command or skill that sets `disable-model-invocation: true` listed `hidden` and not counted; exit 1 over 1,024 B or on a counted file with no description (GUIDE §1) |
| `setup` | the root setup, POSIX `sh`: resolves a link to itself, then execs this checkout's `plugins/suite/bin/agentik-suite setup` with its arguments, from any cwd |
| `scripts/setup-probe [--keep] [--code DIR] [--claude PATH]` | run by hand, never by `make check`: clones this HEAD and the tools' mains into a temp HOME behind a network wall, runs the clone's `setup --yes --json` twice, then `agentik --version`, `setup --dry-run` and `doctor` from what it placed; every new file must be one setup reports or Claude Code's own, and the second run must change nothing |
| `scripts/suite-probe` | run by hand, never by `make check`: clones this HEAD and the three tools' mains into a temp HOME, runs `claude plugin marketplace add` and `install suite@agentik` there with no model reached, reads `installed_plugins.json`, the exec bits and each tool's bare commands against the installed copies, then whether `update` installs a bump, no entry holding a `version`: the probe fails when it does not |
| `scripts/door-probe` | run by hand, never by `make check`: clones, at main, each checkout beside this one that writes the `agentik` door (a plugin launcher's `install-cli`, or the door's line of `make -n install`) into a temp folder and asks whether each leaves a newer door in place: `kept` and `absent` pass or fail; a FIFO, a non-UTF-8 version line and a race against a newer clone are notes |
| `scripts/agentik_install.py` | the canonical `install-cli`: freeze, launcher, prune and forward refresh, generic by name, stdlib at Python 3.9 (GUIDE §10) |
| `scripts/plugin-launcher` | the canonical launcher a plugin keeps in `plugin/bin/agentik-<tool>`; its names come from `plugin/lib/agentik-tool.conf` (GUIDE §10) |
| `scripts/sync <repo>` | copies `bin/agentik`, `scripts/hygiene`, `scripts/recordlint`, `scripts/bounded`, `scripts/plugin-version-check` and `scripts/plugin-description-bytes` into `<repo>/scripts/` and writes `scripts/vendored.sha256`; in a repo with a `plugin/lib/`, also the two above and the door, listed there too |

## The agentik-suite command

The suite's own command, run by its plugin's launcher on the system's Python 3.9 with the standard library alone. Every verb takes `--json` (one object on stdout), `-q`/`--quiet` (no hints), `--no-color` and `-h`/`--help`; stdout carries the answer, stderr the hints and errors; exit 0 done, 1 a check said no or a step failed, 2 usage, 3 not installed. Off a terminal a status is a word (`ok`, `warn`, `FAIL`, `note`), with no escape byte.

| verb | what it does |
|---|---|
| `agentik-suite`, `help`, `-h`, `--help` | the verbs and flags, then each `agentik-*` on PATH by name and path, then one `next:` hint; `help <verb>` or `<verb> --help` for one verb |
| `agentik-suite version`, `--version` | `agentik-suite <version>`, from the plugin's manifest |
| `agentik-suite setup [PLUGIN...]` | with `--dry-run`, the plan for the default set (or the named plugins) in seven steps, each read with its state and the command setup would run: the prerequisites, the `agentik` marketplace, each plugin, each launcher in `~/.local/bin`, the suite's own launcher and the door, `~/.local/bin` on PATH, the doctors; that read writes nothing and starts no process. Without it, setup applies steps 2 to 5 a command at a time, reading the plan again after each, and stops at the first that fails, exit 1. It asks once on a terminal and needs `--yes` off one, where it refuses outright a step that would write a settings file the user's gate list names; it never edits a shell profile (step 6 prints the `export PATH` line) and leaves step 7 to `doctor`. It says what it ran and wrote, and `--json` gives `ran`, `wrote` and `nothing` |
| `agentik-suite config [TOOL[.KEY]]` | each tool (the suite, each `agentik-*` on PATH, each `<name>@agentik` installed) with its state, its settings and how many differ, and its user file; `config <tool>` its settings, the layer each comes from and a mark where it differs; `config <tool>.<key>` one setting: its value, default, the file and line that set it, each layer's value, and the line or block that changes it. `--changed` lists every setting that differs; `--user-files` each user file that travels. A tool answers through its own `describe --json`, run with the others under one 2 s wall and cached by the executable; one that does not answer is read from the suite's table, `plugins/suite/lib/fallback.json`. It writes no setting |
| `agentik-suite describe --json`, `describe config --json [KEY]` | the suite's own answer to that read: `agentik.describe/1`, then `agentik.config/1` for its settings: `checkouts` and `watchers` in `~/.config/agentik/suite/config.yaml`, and `kind` in the `suite` section of a repo's `.claude/agentik/config.yaml` |
| `agentik-suite status [PATH...]` | one screen of five parts in a fixed order, each with one mark (`ok`, `warn` where a hand is needed, `note` where it was read in part): the declared watchers, the live sessions and their helpers, the gate's running, queued and red jobs, the backlog's open steps across the checkouts it covers (the paths given, the user file's `checkouts`, a `kind: hq` repo's folder, or this checkout), and today's runs; then which sources were read and how long they took. Each tool's status read starts at once under its own wall, and each part is printed as soon as it and every part above it is read; a fault is one row and its command one more, never cut. On a terminal a row ends at the width; in a pipe nothing is cut and every byte is ASCII. One hint on stderr when a hand is needed. `--json` gives the `agentik.status/1` object; it writes only the describe cache; exit 0 whenever it ran |
| `agentik-suite status --check` | each watcher declared under `watchers` in `~/.config/agentik/suite/config.yaml` that is not running, one line each with the line that starts it: no process of yours whose command has the watcher's `match` at its head, or a process whose beat file is older than its `fresh_s`. It reads one `ps` listing under a 1 s wall and each beat file, runs no tool, and prints nothing when every watcher runs; exit 1 when it prints a line. `--json` gives every watcher's state |
| `agentik-suite install-cli [--prefix DIR]` | places this command's launcher and the `agentik` door in `DIR/bin` (default `~/.local`), freezing the plugin's tree under `DIR/share`; when `DIR/bin` is off PATH it prints the `export PATH` line. `--dry-run` says what it would do |
| `agentik-suite doctor` | this machine in one read, grouped by tool, the suite's first: the first `agentik` door on PATH and its version, any `agentik-<word>` that would take a verb's place, the user settings file, setup's steps 1 to 6, then each tool's own `doctor` under one deadline. Each check is `ok`, `note`, `warn` or `fail` with the line that mends it; exit 1 when one fails. It writes nothing itself |
| `agentik-suite inbox [REPO...] [NUMBER...]` | what waits on you across the checkouts it covers (the paths given, the user file's `checkouts`, a `kind: hq` repo's folder, or this checkout): the title counts the open questions, the hand lines of each sitting's Waits part and the build-order steps waiting on the owner, then one block a checkout, with its sitting's last word and what was decided without asking. Its three reads run at once under one 5 s wall; a read that gives no answer is one `not read` row, and the count reads `at least`. A number opens that question's block as written; `--check` prints one plain line a thing and exits 1 when there is one; `--json` gives the `agentik.inbox/1` object. It writes only the describe cache and opens no file in a checkout; exit 3 when no command on PATH gives a read |

An unknown verb exits 2 and names the nearest verb or plugin; a plugin's name with no `agentik-<name>` on PATH exits 3 and names `agentik-suite setup --dry-run <name>`. `make voice` holds the messages to their voice; `make check` holds them to what it last passed.

## Make targets

- `make check`: the tests, `sh -n` and the line bound on the front door, the hygiene scan of this repo, the records lint (`scripts/recordlint` on `HANDOFF.md` and `NICE_TO_HAVE.md`), the marketplace check, and `voice-check`, the suite command's catalogue against `design/voice/checked.sha256`.
- `make voice`: the catalogue through the voice scanner, found by `RESPEAK_ROOT` or in Claude Code's plugin cache; on its pass it writes `design/voice/checked.sha256`. Not part of `make check`; with no scanner it exits 2 and writes nothing.
- `make help`: the targets, one line each.
- `make local-marketplace`: writes the marketplace with `file://` urls (one checkout per tool under `AGENTIK_CODE`, default this repo's parent folder) into `AGENTIK_MARKETPLACE_DIR` (default `~/.local/share/agentik/marketplace`), then checks it with `marketplace-check --local`. The published file names public repos only; the local file leaves out `suite` (this Mac installs the tools by name) and adds, after the five, the entries of the overlay `AGENTIK_MARKETPLACE_OVERLAY` (default `~/.config/agentik/marketplace-local.json`, kept outside every repo), a JSON object whose `plugins` are in the published form, for a plugin whose repo is not public. An absent overlay adds nothing; one that cannot be read, is not JSON or has no `plugins` list fails the target, which then writes nothing. `scripts/local-marketplace` does the merge.

## Tests

Python stdlib `unittest`, no venv: `make test` runs `python3 -m unittest discover -s tests`.

## Design of record

[design/agentik-r1.md](design/agentik-r1.md): one command surface, and this repo.

## License

MIT; see [LICENSE](LICENSE).
