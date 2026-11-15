# The hq of this tree

This repo is an hq: the top of a tree of repos. It holds what spans the repos beside it: what is settled, what is open, and what waits on the owner. Their code stays in their own repos.

`agentik init --kind hq` wrote every file here. Each record starts empty, in the shape its tool reads.

## Start here

1. Run `make check`. It passes on the files as written.
2. Make the first commit, by path:
   `git add README.md CLAUDE.md DECISIONS.md OPEN-QUESTIONS.md HANDOFF.md NICE_TO_HAVE.md Makefile .gitignore .claude scripts history`,
   then `git commit -m "The hq, as agentik init wrote it"`.
3. Give this page its tree's name, and list the tree's repos under "The repos" below. That is row 1 of `HANDOFF.md`.
4. Keep the tree's repos beside this one, in the same folder. An hq stands for the git checkouts in its folder. `agentik inbox` and `agentik status` are the reads that take every checkout beside this repo.
5. Start `claude` in this folder for the first sitting. `agentik session charter open "<the goal>"` writes its charter in `history/sittings/`.

## What each file holds

| file | what it holds | how it changes |
|---|---|---|
| `DECISIONS.md` | what is settled for the tree, one entry a line | `agentik decisions answer`, on the owner's answer |
| `OPEN-QUESTIONS.md` | what waits on the owner's word, each with a recommended answer | `agentik decisions new` adds one; `agentik decisions ask` asks them |
| `HANDOFF.md` | the build order, one row an item | by hand; `agentik decisions backlog .` reads it |
| `NICE_TO_HAVE.md` | findings that block nothing | by hand, one row a finding |
| `history/sittings/` | one charter a sitting, the newest live | `agentik session charter open` |
| `CLAUDE.md` | what every sitting here is told | the top by hand; the block by `agentik decisions render` |
| `.claude/agentik/config.yaml` | `suite: kind: hq`, which says this repo is an hq | by hand |
| `Makefile`, `scripts/recordlint` | the check | never by hand: `scripts/recordlint` is agentik-commons' copy |

## How a decision is made

A question goes to the owner before it binds anything. `agentik decisions new` files it in `OPEN-QUESTIONS.md` with a recommended answer. The owner answers. `agentik decisions answer` then writes the entry in `DECISIONS.md`, and `agentik decisions render` brings `CLAUDE.md` up to date. A choice that is easy to undo is made by whoever meets it. It is noted under "Decided without asking" in `OPEN-QUESTIONS.md`.

## The check

`make check` runs two checks. `scripts/recordlint` holds `HANDOFF.md` and `NICE_TO_HAVE.md` to their tables. `agentik decisions render --check` compares the block in `CLAUDE.md` with `DECISIONS.md`. Run it before each commit.

## The repos

None is listed yet.
