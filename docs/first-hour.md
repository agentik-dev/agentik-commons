# The first hour

Two short tasks for a machine that `agentik-commons/setup` has just set up, about ten minutes each.
The slash commands need nothing more. The terminal lines need `~/.local/bin` on your PATH, the line setup printed; without it, type `~/.local/bin/agentik` in place of `agentik`.

Both tasks run in a scratch repo, so nothing here touches a repo of yours:

```sh
mkdir agentik-try && cd agentik-try && git init
```

## 1. Read the budget

Start `claude` in that folder and ask it to list the files and say what the repo is.
The line above the prompt changes to something like `session: fable 5.2 · 1M · ctx 4% · turns 1%`: the model, its window, and the share of context and of turns used.
`/session:status` gives the same figures and the zone they fall in.
`/agents:status` gives a table with one row for each session: its model, turns, context, cost and last tool. A second `claude` in another tab makes two rows.
The default profile also asks a session to keep a short charter, a file under `history/sittings`; here that file goes in the scratch repo.

Leave the session, then in a terminal:

```sh
agentik session report
```

It has one row for the session you just ended. Before any session has ended it prints `the ledger is empty` and exits 2.

What this shows: what a session costs, and how far it is from its stop, while it runs.

## 2. Settle one thing, and a new session obeys it

In the same folder:

```sh
agentik decisions init
```

It writes `DECISIONS.md` with three empty sections and a short generated block in `CLAUDE.md`, and it lists both files in `.claude/edit-gates`. From then on a session changes them through `/decisions:instruct`, never by its own edit; deleting a file's line in that list lifts the gate.

Record a question, then answer it:

```sh
agentik decisions new --title "Indent" --stands "Files mix both." --choice "Which indent here?" --option "Spaces: all files move to four spaces" --option "Tabs: all files move to tabs" --recommend "Spaces: most files use them."
agentik decisions answer 1 --pick Spaces --source "me" --text "This repo indents with four spaces." --area "Every session" --every-turn
```

The second prints ``answer: 1, Spaces; entry 1 under `### Every session` in DECISIONS.md``, then a line saying it rewrote the block in `CLAUDE.md`, now 65 bytes longer. `--every-turn` says you accept that this entry is loaded on every turn of every session in the repo.

Start a new `claude` and ask "how do we indent here?": it answers from entry 1. Ask it to edit the rule in `CLAUDE.md` directly: the edit is refused, and the refusal names `/decisions:instruct`.

What this shows: a ruling made once reaches every later session, in 65 bytes, and stays as written.

## When you are done

Delete the `agentik-try` folder. The [agentik](https://github.com/agentik-dev) page says what each plugin does and how to leave.
