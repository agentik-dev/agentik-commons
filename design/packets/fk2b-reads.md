# Packet fk2b-reads: the doctor and `config` say which source stands, and a fork's name stays under one key

| item | value |
|---|---|
| from | agentik-hq's brief fk2b-reads of 2026-11-13, R1 to R8, and the coordinator's start line of 2026-11-14; hq design/25 §3 items 2, 9, 10, 11, 13, 15 and 16; level S3 |
| pin | main at 82d634b (suite 0.7.5: fk2-plan and sc3-table landed); worktree `.claude/worktrees/fk2b-reads`, branch `fk2b-reads`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` process, no agent; made-up names (`murmur`, `acme-tools`); no version (the start line: sc13 and rp8 land first) |
| may touch | `plugins/suite/lib/agentik_suite/doctor.py`, `config.py`, `apply.py` (`gated` takes the file), `messages.md` (`## Doctor`, `## Config`); `tests/test_fk2b_reads.py` (new); `NICE_TO_HAVE.md` (one row); `design/voice/checked.sha256`; this packet; `history/sittings/2026-11-14-7.md` |
| verify | `make voice`, then `make check`, each once, last, through the gate queue, `--strict` |
| acceptance | 1 to 10 below; `python3 -m unittest tests.test_fk2b_reads` OK |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. The finding, measured again at 82d634b

The brief's red for line 1 differs: T is outside the default set (`session`, `decisions`, `agents`), so `doctor.plan_rows` never names it, and in every home `doctor --json` holds no `acme`. The leak is `config --json`'s `path` in hD, hI and each home with a fork's command (`~/.claude/plugins/cache/acme-tools/...`); and, with the homes built for `session`, a name of the default set, hA's check is named `plugin session@acme-tools` and hE's detail holds `0.12.6-acme.1`; hI's held row reads `not placed`. No screen has a `from`, `seen` or `runs` line; hB's `config` row is `note murmur no command`; `config suite.sources.murmur` in hB is refused, `suite has no key sources.murmur`, exit 2; `doctor` in hJ names neither the gate nor `paint`'s folder. Line 7's `config --changed` in hJ already lists `suite.sources.murmur`.

## 2. Rulings

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. A source is the finder's row (`sources.find`); not own means `kind` is `plugin`, `folder` or `undecided`.

- R1 (item 15). `doctor --json`'s tool group and `config --json`'s tool row gain `source`, the whole row, null for the suite. What a source that is not own gives (id, marketplace, folder, version) stands in no check's `name`, `detail` or `remedy`, and in no other key of a row: `plan_rows` names such a step 3 by its tool and gives it doctor's own words; `config --json`'s `path` is null where the file lies under such a source's root. Every `from`, `seen`, `runs` and `passed over` line is made at print time from `source`.
- R2 (item 10). Under the group line of a tool whose kind is `plugin` or `folder`: `from <id or folder> <version>,` then `the only plugin of that name` or `declared at <path>:<line>`, the path from `~`. Where `runs.path` is not under the root, one more line names that file, its version and what it is. A note, printed with and without `--all`; no fold removes it. A version is the source's string, never called behind or newer.
- R3 (item 16). Own sources with `mirror` true: one `from` note in the suite's group, for all such tools.
- R4 (items 9, 10), warns, none changing the exit: `undecided` (`N plugins of this name are installed, and no source is declared`, a `seen:` line, the remedy and the close `agentik config suite.sources.T`; a lone repo plugin and one id twice get their own words); declared, not found; declared with a `seen` (two plugins are named T); each config-read warning of reason `value`, `ignored`, `self` or `relative`, with its file and line; `passed_over` (the file named on the screen, in no detail); a held plan row's remedy `agentik config suite.sources.T`.
- R5 (item 2). While `sources` holds a line and the user file is on no gate list (`${CLAUDE_CONFIG_DIR:-~/.claude}/edit-gates`, read by `apply.gated`, which takes the file), the suite's group warns `sources` and prints the line to add, the file's path. No verb writes the list.
- R6 (item 11). `config`'s row and the title of `config T` end `from <id or folder>` for kind `plugin` or `folder`; an `undecided` row reads `T  N plugins of this name; no source is declared`, a warn; `config T` for it prints a card: the count, `seen`, `edit <user file>` with `sources:` and `  T: <an id of seen>`, `takes hold now`. `config suite.sources.T` prints that card for any tool the suite knows while no line is written, the setting's own card once one is.
- R7 (item 13). A source that stands and ships no command reads as at the pin (`note`, no command), with the `from` line; one whose command gives no counted answer as at the pin, with the `from` line.
- R8, not built: `sources.py`, `plan.py`, `tools.py`, setup's screens; item 14's line for a tool with a row in `fallback.json`.

## 3. Acceptance

T is `murmur` (line 1 also `session`); U `T@agentik`; F `T@acme-tools`; the homes are `tests/fk_homes.py`'s with `ready()`; a set-up home also has the suite's launcher and the door in `~/.local/bin`.

| # | line |
|---|---|
| 1 | every home, T `murmur` and `session`: `doctor --json` and `config --json` hold `acme` in no check's `name`, `detail`, `remedy` and in no key of a row but `source`; hE's `0.12.6-acme.1` included. Pin: `plugin session@acme-tools`; hD's `path` |
| 2 | hD `doctor`, with and without `--all`: `from murmur@acme-tools 0.12.6, the only plugin of that name`; hJ: `declared at ~/.config/agentik/suite/config.yaml:2`. Pin: no line |
| 3 | hI, set up: the `undecided` warn, `seen:` with both ids and versions, `runs ~/.local/bin/agentik-murmur 0.12.6, a placed launcher of no known source`; exit 0; the close names `agentik config suite.sources.murmur`. Pin: `ok murmur`, close `setup` |
| 4 | hJ: the gate warn in the suite's group; gone with the path in `<home>/.claude/edit-gates`; `paint` a warn. Pin: none |
| 5 | hJ's repo folder: a warn naming its file and `suite.sources`'s line; a user file with `sources.suite`, one with `./fork`, one under a relative `XDG_CONFIG_HOME`: a warn each. Pin: none |
| 6 | hB, a command under each root, both `bin/` on PATH: the passed-over warn; the file on the screen, in no `detail`. Pin: none |
| 7 | `config`: hD's row ends `from murmur@acme-tools`; hB's row is the `undecided` warn; `config murmur` and `config suite.sources.murmur` in hB print the card with the block; `config --changed` in hJ lists `sources.murmur`. Pin: the last only |
| 8 | hF with a made-up `agentik` source: one `from` note in the suite's group. Pin: none |
| 9 | hA: T's row a note with the `from` line; no `not installed`. Pin: the note, no line |
| 10 | `make voice`, then `make check`, green |

## 4. Not built

The reason beside `did not answer` and the `tool` equality (ak9b); what an issue report gathers and scrubs (fk6); the screens' forms where sc10, sc6 or sc8 land later; the version (a later word).
