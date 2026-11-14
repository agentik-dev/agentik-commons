# Packet sc4-errors: a refusal is the cause and then the command, and `config session effort` is `config session.effort`

| item | value |
|---|---|
| from | agentik-hq's brief sc4-errors of 2026-11-13, R1 to R8; hq design/23 §4, §7, §8 and §9 (row sc4-errors); level S2 |
| pin | agentik-commons main 88d25d2 (`Merge fk1-sources`, suite 0.6.5; sc2-name landed); worktree `.claude/worktrees/sc4-errors`, branch `sc4-errors`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync into another repo; no bare `make`; no relay verb or binary; no `claude` process; made-up names in fixtures; the door (`bin/agentik`) is sc13's; no version in the first build |
| may touch | `plugins/suite/lib/agentik_suite/{term,cli,config}.py`; `plugins/suite/lib/agentik_suite/messages.md` (`## Errors`); `design/voice/checked.sha256` (by `make voice` only); `tests/test_sc4_errors.py` and the older tests that assert a refusal's or a hint's words (`tests/test_{agentik_suite,suite_word}.py`); `NICE_TO_HAVE.md`; this packet; `history/sittings/2026-11-13-17.md` |
| verify | `make voice`, then `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 9 below; `python3 -m unittest tests.test_sc4_errors` OK; verify green |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls. `claude-opus-5-5` |

The repo keeps no `DECISIONS.md`; `GUIDE.md` binds. Cited: hq entry 6 (stdlib at Python 3.9), hq entry 37 (made-up names).

## The owner's words

2026-11-12: "Make it a high quality modern CLI tool that is dynamic and has high quality concise human friendly feedback". And: "Make plugin configuration discoverable and drill down."

## Measured at suite 0.6.2

1. `agentik config session effort`: `FAIL  agentik-suite config takes no argument, and got effort. Run agentik-suite config --help for its usage.`, exit 2. It takes one, and `config session.effort` prints the card.
2. `agentik sesion`: `FAIL  sesion is not a verb; the nearest is session. Run agentik-suite --help for the list.` `session` is a tool, and that list holds none.
3. `agentik config turns`: `turns is not a tool here; the nearest is agents.` The nearest is offered at any distance.
4. `agentik confg --json`: `error.message` is the whole sentence, the command inside it, and `error.remedy` is `agentik-suite config`.
5. In a pipe every hint starts with two labels, `note  next:`, and what follows is a sentence, not a command.

## Rulings

- R1, the form. A refusal is two lines on stderr: the cause, behind `t.error`'s mark, then `next: ` and one command, with no mark. A refusal with no command is the cause alone. `Term.error` takes the command and writes both; `Term.hint` writes its message with no mark before it, on a terminal and off, dim as now.
- R2, `--json`: `error.message` is the cause, `error.remedy` the command or null, `error.code` as at the pin. Every exit is the pin's: 2, and 3 for the table's two `paint` rows.
- R3, whose. Every refusal raised in `cli.py` and `config.py` takes the table's words. One raised in `apply.py`, `install.py` or `status.py` keeps the pin's one line, with no second line, until its own row turns it; `Usage` says which, by a mechanism of yours.
- R4, the command. Where a near word exists, it is the line as typed with that one word mended, from `cmd.say`, each word quoted by `shlex`. Near is `difflib` at the cutoff of 0.6 the verbs use, for verbs, tools, flags and keys alike; `config`'s cutoff of 0 goes. A mended tool's name with no word after it gives `help <tool>`, since a tool run bare is a usage error.
- R5, the words after `config` are one path. They are joined with dots before anything is read: `config session effort` is `config session.effort`, and `config session budget turns` is `config session.budget.turns`. Every line the command prints writes the dotted form. With `--changed` or `--user-files` a name is refused, as at the pin.
- R6, a word that is no verb. The near word is looked for among the verbs and the listed tools that have a command. Near a verb: `is not a verb`. Near a tool: `is not a tool`. Near neither: `is not a verb or a tool`.
- R7, the table. `murmur` and `paint` stand for a tool and a plugin; a cause ends with no full stop and holds no command. `agentik` stands for what `cmd.say` gives.

| typed | cause | next |
|---|---|---|
| `confg`; `confg suite.kind` | `confg is not a verb` | `agentik config`; `agentik config suite.kind` |
| `murmr`; `murmr list` | `murmr is not a tool` | `agentik help murmur`; `agentik murmur list` |
| `zzz` | `zzz is not a verb or a tool` | `agentik help` |
| `paint`, installed, no command | `paint is a plugin with no command` | `agentik config paint` |
| `paint`, known, not installed | `paint is not installed` | `agentik setup paint` |
| the suite by its own name, `murmur` | `murmur is a tool, not a verb` | the tool's file through `prog.shown`, then `--help` |
| `config --jsno` | `--jsno is not a flag of config` | `agentik config --json` |
| `config --zzz`; `--zzz` | `--zzz is not a flag of config`; `--zzz is not a flag` | `agentik help config`; `agentik help` |
| `--help --version`; `doctor --version` | `--version takes no verb and no --help` | `agentik --version` |
| `doctor extra` | `doctor takes no name; extra is one more` | `agentik help doctor` |
| `help config extra` | `help takes one name; extra is one more` | `agentik help help` |
| `config --changed suite` | `config --changed takes no name; suite is one more` | `agentik config --changed` |
| `config --changed --user-files` | `--changed and --user-files are two answers` | `agentik config --changed` |
| `config murmr`; `config murmr width` | `murmr is not a tool here` | `agentik config murmur`; `agentik config murmur.width` |
| `config zzz` | `zzz is not a tool here` | `agentik config` |
| `config murmur.widht` | `murmur has no key widht` | `agentik config murmur.width` |
| `config murmur zzz` | `murmur has no key zzz` | `agentik config murmur` |
| `config .width`; `config murmur.` | `a tool's name goes before the dot`; `a key goes after the dot` | `agentik config`; `agentik config murmur` |
| a key of a tool that gave no keys | the pin's clause up to its first full stop, `settings` read as `keys` | `agentik config murmur` |
| a file that does not parse | the fault: its path, line and reason | none |
| `describe` | `describe prints JSON for other tools, so it needs --json` | `agentik describe --json` |
| `setup Bad_Name` | `Bad_Name is not a plugin name: lowercase letters, digits and dashes` | `agentik setup --dry-run` |
| `version`, no manifest | `agentik has no version: <path> cannot be read` | `claude plugin install suite@agentik` |

- R8, the catalogue. Each message under `## Errors` that the table turns is the cause alone; its remedy's sentence and the slots only that sentence used go. `err.status.*` stay byte for byte. Each cause holds to design/23 §8: at most 76 characters before its values, `key` and never `setting`, no `exit`, no code.
- Not yours: any hint's words (each screen's own row); `term.table` (sc3); setup's, install's and status's refusals; the search by a bare word that is no tool (sc7), which keeps `is not a tool here`; the door.

## Acceptance

In a temp HOME under `env -i` with the door and the suite on PATH, a stub tool `murmur` that answers the config read with keys `width` and `paint.colour`, and a plugin `paint` installed with no command.

| # | line | at the pin |
|---|---|---|
| 1 | `config murmur width` prints the stdout bytes of `config murmur.width`, exit 0; `config murmur paint colour` those of `config murmur.paint.colour`; no line of either holds `murmur width` | `takes no argument`, exit 2 |
| 2 | each row of R7's table: stderr is its cause behind `FAIL  ` and then `next: ` and its command, or the cause alone; stdout empty; the exit as at the pin | one sentence |
| 3 | each row with `--json`: `error.message` is the cause, `error.remedy` the command, `error.code` as at the pin | the sentence in `message` |
| 4 | each `next:` of line 2, pasted into `sh -c` with stdin closed, exits other than 127 | |
| 5 | `config turns`, where no tool is within the cutoff: the cause names no other tool and the next is `agentik config` | `the nearest is agents` |
| 6 | on a terminal the cause's line starts with the fail glyph and the second line with `next:`; a hint in a pipe starts `next:` with no `note` before it | `note  next:` |
| 7 | a refusal of `setup` raised in `apply.py`, and `install-cli --prefix` with no folder: one line each, the pin's bytes | holds |
| 8 | under `## Errors`, outside `err.status.*`: no message holds `Run `, `Mend`, `nearest` or `exit`, none ends in a full stop, none passes 76 characters before its values | 22 of 22 hold `Run ` or `Mend` |
| 9 | `make voice` green, its sidecar committed; the full suite under `/usr/bin/python3`; `make check` once, last, through the gate queue | |

Rules: tests first, seen red at the pin. Tests name made-up tools and plugins only: the hygiene scan refuses the sibling tools' names in a test. A first build sets no version; phase 2 names it. `make voice` runs before `make check`. Where a test of another row asserts `note  next:`, change it in the commit that changes `Term.hint`.

Left: each hint's words as a command alone (sm2, sc5, sc6, sc8, sc10); the refusals of setup, install and status (sc8, sc11, su2); `config <word>` as a search (sc7).

## Baseline, measured at 88d25d2

`tests/test_sc4_errors.py` at the pin: 9 of 10 red, line 7 green. Each row of R7's table exits as above at the pin (2, and 3 for both `paint` rows), and `--json`'s `error.code` is the table's, but for the rows R5 turns: `config murmr width`, `config murmur zzz` and `config paint width` are `extra_word` at the pin (`config takes no argument`), and become `unknown_tool`, `unknown_key` and `no_answer`. `describe --json` answers, exit 0, so the `describe` row has no JSON line. `config turns` offers `murmur` at the pin.

## Interfaces

`cli.Refusal(Usage)`: the two-line form; `Usage` itself keeps the pin's one line for apply.py, install.py and status.py (R3). `Command.mend(index, *words)`: the typed line with the word at argv's `index` replaced by `words`, through `cmd.say`. `Term.error(mid, command=None, **values)`. `config.path(nouns)`: the words joined by dots.
