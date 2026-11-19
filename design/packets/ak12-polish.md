# Packet ak12-polish: `agentik completion zsh|bash`, and the suite's skill for the command

| item | value |
|---|---|
| from | agentik-hq's brief ak12-polish of 2026-11-19, R1 to R8, on the row's design D1 to D8; hq design/15 §9's row (`completion zsh\|bash`, one skill in `suite` under the description cap); level S3 |
| pin | agentik-commons main 10ef20e (suite 0.7.36); worktree `.claude/worktrees/ak12-polish`, branch `ak12-polish`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no tool synced; no test reads the live home or state; made-up names in fixtures |
| may touch | `plugins/suite/lib/agentik_suite/cli.py`, `plugins/suite/lib/agentik_suite/completion.py` (new), `plugins/suite/lib/agentik_suite/tools.py`, `plugins/suite/lib/agentik_suite/term.py`, `plugins/suite/lib/agentik_suite/messages.md`, `plugins/suite/skills/suite/SKILL.md` (new), `plugins/suite/.claude-plugin/plugin.json`, `design/voice/checked.sha256`, `tests/test_ak12_completion.py` (new), `tests/test_ak9c_plug_rest.py` (`completion` now a verb), `tests/test_sc5_first_screen.py` (`PIN_KEPT` re-pinned: two ids of the verb, six flags' messages), `GUIDE.md` (§10), `README.md`, `NICE_TO_HAVE.md`, `history/NICE-overflow.md`, `design/packets/ak12-polish.md`, `history/sittings/*.md`, `history/sessions/NEXT` |
| verify | `python3 -m unittest tests.test_ak12_completion` and the touched tests directly; `scripts/plugin-description-bytes plugins/suite`; `make voice` and `make check` once each, last, through the gate queue; `scripts/hygiene --require-private` on the tree and on `--commits main..HEAD` |
| acceptance | 1 to 11 below |

## 1. The finding

hq design/15 §9 owes the command a completion and the suite plugin one skill for the command. At the pin `agentik-suite completion zsh` exits 2 (`completion is not a verb or a tool`), though `doctor.py` `RESERVED` keeps the word; the suite plugin holds one skill, `issue`, 131 of 1,024 B.

## 2. Rulings

- R1, the verb: `completion` joins `VERBS`. `completion zsh|bash` prints the script, exit 0; `--json`, `agentik.completion/1` with `shell` and `script`. Bare, a third shell or a word after the shell: the two-line refusal, exit 2, `next:` `help completion`. It writes nothing. `help completion` shows `eval "$(agentik completion zsh)"` for `~/.zshrc` and the bash line for `~/.bashrc`. The first screen does not change by a byte.
- R2, the callback: `completion words -- WORD...` prints `name<TAB>summary` a line for the last WORD, the earlier ones its context, filtered by its prefix; `--json`, `words: [{name, summary}]`. Exit 0 whatever the words, none included; nothing printed where nothing is offered; the words after `--` are never this command's flags.
- R3, a Tab starts no tool: a tool's summary and verbs come only from the describe cache where the stamp matches.
- R4, the tables are the source: `VERBS`, `FLAGS`, `VERB_FLAGS`, `VALUE_FLAGS`, `issue.WORDS`, `plan.known`, `tools.installed`, the finder's listing as `_tools(survey=False)` reads it, and `init.kinds` after `--kind`; the test hooks `--ps` and `--now` named once, as `HOOKS`, and left out; a flag on the line is not offered again; a flag with no `flag.*` message gets one.
- R5, data and not shell text: a name that is neither a `NOUN` nor a flag of the tables is not printed; a summary goes through `tools.one_line` and `tools.plain`, loses any tab, and is cut to 80 columns; the scripts hold no `eval`, `compgen -W` or unquoted expansion of what came back.
- R6, the scripts: each calls the command as the line names it with stderr dropped, sends the words up to the cursor, and falls to file completion on an empty answer. bash 3.2: `complete -o default -F`. zsh: `#compdef agentik agentik-suite` first; a function file completes, evaluated it registers, loading `compinit` where no `compdef` exists. Both register `agentik` and `agentik-suite` alone.
- R7, the skill: `plugins/suite/skills/suite/SKILL.md`, `name: suite`, D8's description (185 B), a body under 60 lines holding D8's three rules and the pointer to the `issue` skill; every `agentik ...` line in it one the suite takes.
- R8, the words: new messages pass `make voice`; GUIDE §10 and the README name the verb; D7's leads are rows in `NICE_TO_HAVE.md`; suite 0.7.37 in the last commit; the door does not change.

## 3. Interfaces

- `agentik-suite completion words -- WORD...`: stdout `name\tsummary\n` lines, exactly one tab a line, no escape byte; `--json`: `{"schema": "agentik.completion/1", "ok": true, "words": [{"name", "summary"}]}`.
- `agentik-suite completion zsh|bash --json`: `{"schema": "agentik.completion/1", "ok": true, "shell", "script"}`.
- `term.Term.verbatim(text)`: text on stdout as the caller made it, the one writer's road for a script and the callback's lines.
- `tools.cached(name, exe, env)`: the counted describe in the cache whose stamp matches `exe`, else None; it starts nothing.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `-k Scripts`: `completion zsh` and `completion bash` exit 0; `zsh -n`, `bash -n` take what they print | exit 2, not a verb |
| 2 | `-k BashDriver`: `/bin/bash --norc --noprofile`, the function against the real command, two made-up tools cached: first word, `se`, `setup --d`, a tool's verbs, mid-line, `complete -p` | no verb |
| 3 | `-k ZshDriver`: `zsh -f`, `$_comps` for both names, the same five lines through recorders, an empty answer to `_files` | no verb |
| 4 | `-k NoProcess`: ten lines start no tool's launcher; a stale or absent cache: the name, no summary, no verbs | no verb |
| 5 | `-k Hostile`: one tab a line, no escape byte, `a;b` not printed, no marker after either driver | no verb |
| 6 | `-k Tables`: each verb's offered flags are its tables' less the hooks, each passes `_flag_fault`; a flag added later is offered | no verb |
| 7 | `-k Refusals`: bare, `fish`, `zsh more` exit 2 in two lines naming `help completion`, `--json` the error; `words` alone exit 0, no byte | exit 2, not a verb |
| 8 | `-k Skill`: `scripts/plugin-description-bytes plugins/suite` exit 0; the description at most 200 B; each `agentik ` line not `cli.refused`; at most 60 lines | exit 0, 131 B, one skill |
| 9 | `-k Screens`: the first screen unchanged; `help --json` lists `completion` | `completion` absent |
| 10 | not a test: `completion words -- ''` timed three times through the worktree's door on a temp PATH | |
| 11 | `make check` through the gate queue | green at 10ef20e |
