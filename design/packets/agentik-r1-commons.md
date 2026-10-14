# Packet agentik-r1-commons: the front door, the canonical hygiene with `renamed`, the `agentik` marketplace, the guide

| item | value |
|---|---|
| from | `design/agentik-r1.md` §3, §5.2, §6.1, §7, §9 (A1, A9), §10 (D1, D3); step 0 landed in the owner's ledger (2026-10-13). The builder reads THIS packet, those sections, and the read-only sources in §5; nothing else |
| pin | `main` at this packet's commit or later; branch and worktree `agentik-r1-commons`, off main |
| wall | this repo only. No push, no `--amend`, no rebase; no network; no `claude plugin` command (the P1 proof is the observer's, at the switch); never run `relay run`, `plan`, `gate`, `stop`, `kill`, `clean` or `resume`, and never build or run a relay binary |
| may touch | `bin/agentik`, `scripts/{hygiene,bounded,sync,marketplace-check}`, `tests/*`, `.claude-plugin/marketplace.json`, `GUIDE.md`, `docs/sibling.md`, `Makefile`, `LICENSE`, `.hygiene-allow`, `.gitignore`, `README.md`, `NICE_TO_HAVE.md`. Nothing under `design/` but this packet's §6 report, appended |
| budget | 120 turns, 150k context; commit per act; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says

- **§3, the front door.** POSIX `sh`, under 100 lines. `agentik <tool> args…` checks `<tool>` against `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, then `exec`s `agentik-<tool>` from PATH with the args unchanged; it reads and writes nothing and resolves no old name. `agentik` or `agentik help` lists each `agentik-*` on PATH, first in PATH order winning; `agentik help <tool>` runs the tool's `--help`; `--version` prints the front door's version. Exit 0 for list, help and version even when nothing is found; the tool's own code on dispatch; 2 for usage (a bad tool name included); 3 when `agentik-<tool>` is not on PATH, with one stderr line naming the repo `agentik-dev/agentik-<tool>`.
- **§6.1, `renamed`.** A new group in the canonical `scripts/hygiene`, scanning live files only: tracked or untracked-not-ignored, outside `design/`, `bugs/`, `history/`, `NICE_TO_HAVE.md` and `CHANGELOG*`, except that `history/sessions/PROMPT-*`, `history/sessions/BRIEF-*` and each chain's newest charter are live. Patterns: `(?<![\w-])claude-code-(session|decisions|respeak|agents)`, `agent-relay`, `claude-session`, `claude-(api-agent|local|fanout|costs|agents)\b`, `\blocalrig\b`, `\bagentroute\b`, and a backtick directly before `relay ` or `decisions ` followed by a lowercase verb.
- **§6.1, exit codes for the whole scanner.** 0: no hit outside the allowlist. 1: a hit. 2: usage, git failing, a bad private-list line, or `--require-private` without a readable list. Today's copy has 1 and 2 the other way round.
- **§5.2, the marketplace.** `.claude-plugin/marketplace.json`, named `agentik`, five entries `{"source":"git-subdir","url":"https://github.com/agentik-dev/agentik-<tool>.git","path":"plugin"}` with versions, checked by `scripts/marketplace-check`. `make local-marketplace` writes the same file with `file://` urls (each checkout under `$(AGENTIK_CODE)`, default the parent of this repo) into `$(AGENTIK_MARKETPLACE_DIR)`, default `~/.local/share/agentik/marketplace/`, so the IDs match (D1).
- **§7.1–§7.3, the layout, the guide and shared code.** `GUIDE.md` takes over agentik-session's `design/conventions.md` §1–§9 (renamed to the new names) and adds §7.2's table (naming, verbs, exit codes, docs, README shape, install and hygiene). `docs/sibling.md` holds decisions' sibling paragraph. Each tool repo vendors `scripts/{agentik,hygiene,bounded}` with a sha256 pin checked by its own `make check`; `scripts/sync <repo>` refreshes the copies in a packet.
- **A9.** Commons is the tools' shared ground and builds no tool: no `install` target, no plugin of its own.

## 2. Rulings (decided inside the design; logged here, one sentence each)

1. **The pin file.** `scripts/sync <repo>` copies `bin/agentik` to `<repo>/scripts/agentik` and `scripts/{hygiene,bounded}` to `<repo>/scripts/`, then writes `<repo>/scripts/vendored.sha256` in `shasum -a 256 -c` form; each repo's packet adds that check to its `make check`. A file the Makefile checks keeps the record's intent and keeps the Makefile free of hashes.
2. **The newest charter.** A charter is `history/sittings/<YYYY-MM-DD>-<n>[-<chain>].md`; per chain (the suffix, empty included) the one with the greatest (date, integer n) is live. Integer order, never lexical: `-10` is newer than `-9`.
3. **Tests.** Python stdlib `unittest`, run by `make test` as `python3 -m unittest discover -s tests`, so commons needs no venv. `tests/test_hygiene.py` comes over from agentik-session with its exit codes swapped and gains the `renamed` cases; `tests/test_agentik.py` drives `bin/agentik` through `subprocess` with a scratch PATH.
4. **`make check`.** `test`, `hygiene` (on this repo), `marketplace-check`, `sh -n bin/agentik`, and the line count of `bin/agentik`. No doclint until r2.
5. **Versions in the marketplace.** Each entry's version is read from that repo's `plugin/.claude-plugin/plugin.json` on its main today; `marketplace-check` validates shape (name `agentik`, five entries, the five names, each url and path, semver versions) and never reads the network.
6. **Allowlist.** Each `.hygiene-allow` row carries a `#` reason line: `scripts/hygiene` and `tests/test_hygiene.py` for `renamed` (its own patterns), `GUIDE.md` for the alias paragraph, and `sibling` wherever commons names the five tools by design.

Any further fork: decide inside the record and log it in §6's report; escalate only a contradiction with the record.

## 3. Interfaces

| item | contract |
|---|---|
| `bin/agentik` | as §1; `#!/bin/sh`, under 100 lines, `sh -n` clean |
| `scripts/hygiene` | today's flags (`--json`, `--allow`, `--repo`, `--require-private`) and output, the new group `renamed` in `--json`'s `groups`, the exit codes of §1 |
| `scripts/sync <repo>` | §2 ruling 1; exit 0 done, 2 usage or a missing target |
| `scripts/marketplace-check [file]` | default `.claude-plugin/marketplace.json`; exit 0 valid, 1 a check said no, 2 usage |
| `make local-marketplace` | writes `$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json`, one `file://` url per entry, then runs `marketplace-check --local` on it |

## 4. Acceptance

Each line is run in the worktree after the last commit and reads as given.

| # | line | reads |
|---|---|---|
| 1 | `make check >/dev/null 2>&1; echo $?` | `0` |
| 2 | `PATH=/usr/bin:/bin bin/agentik nosuch 2>/dev/null; echo $?` | `3` |
| 3 | `PATH=/usr/bin:/bin bin/agentik nosuch 2>&1 >/dev/null \| grep -c 'agentik-dev/agentik-nosuch'` | `1` |
| 4 | `d=$(mktemp -d); printf '#!/bin/sh\necho "$#:$1:$2"\nexit 7\n' > $d/agentik-x; chmod +x $d/agentik-x; PATH=$d:/usr/bin:/bin bin/agentik x 'a b' c; echo $?; rm -r $d` | `2:a b:c` then `7` |
| 5 | `d=$(mktemp -d); printf '#!/bin/sh\n' > $d/agentik-x; chmod +x $d/agentik-x; PATH=$d:/usr/bin:/bin bin/agentik \| grep -cw x; rm -r $d` | `1` |
| 6 | `bin/agentik 'X;y' 2>/dev/null; echo $?` | `2` |
| 7 | `head -1 bin/agentik; [ $(wc -l < bin/agentik) -lt 100 ] && echo short` | `#!/bin/sh` then `short` |
| 8 | `d=$(mktemp -d); git -C $d init -q; mkdir -p $d/design $d/history/sessions; for f in a.md design/x.md history/sessions/PROMPT-x.md; do printf 'agent-rela%s\n' y > $d/$f; done; git -C $d add -A; scripts/hygiene --repo $d --json \| python3 -c 'import json,sys;print(json.load(sys.stdin)["groups"]["renamed"]["files"])'; scripts/hygiene --repo $d >/dev/null 2>&1; echo $?; rm -rf $d` | `2` then `1` |
| 9 | `d=$(mktemp -d); git -C $d init -q; mkdir -p $d/history/sittings; printf 'clean\n' > $d/history/sittings/2026-10-13-9-x.md; printf 'claude-sessio%s\n' n > $d/history/sittings/2026-10-13-10-x.md; printf 'x\n' > $d/.hygiene-live; git -C $d add -A; scripts/hygiene --repo $d --json \| python3 -c 'import json,sys;print(json.load(sys.stdin)["groups"]["renamed"]["files"])'; rm -rf $d` | `1` |
| 10 | `scripts/hygiene --nosuch >/dev/null 2>&1; echo $?` | `2` |
| 11 | `python3 -c 'import json;d=json.load(open(".claude-plugin/marketplace.json"));print(d["name"], " ".join(sorted(p["name"] for p in d["plugins"])))'` | `agentik agents decisions relay respeak session` |
| 12 | `d=$(mktemp -d); make local-marketplace AGENTIK_MARKETPLACE_DIR=$d >/dev/null; grep -c 'file://' $d/.claude-plugin/marketplace.json; rm -r $d` | `5` |
| 13 | `d=$(mktemp -d); git -C $d init -q; scripts/sync $d >/dev/null; (cd $d && shasum -a 256 -c scripts/vendored.sha256 \| grep -c ': OK$'); rm -rf $d` | `3` |
| 14 | `grep -c 'Exit codes report the task, not the content' GUIDE.md; grep -c 'agentik-<tool>' GUIDE.md \| awk '$1>0{print "named"}'` | `1` then `named` |
| 15 | `test -s docs/sibling.md && echo ok; grep -c '^install:' Makefile` | `ok` then `0` |
| 16 | `git status --short \| wc -l` | `0` |

The three tests that fail before the change: line 2 (no `bin/agentik`), line 4 (no dispatch), line 8 (no `renamed`, and a hit exits 2 today). Line 9 reads `0` under a lexical sort, since only the `-10` charter holds the hit, and `0` without the `.hygiene-live` that declares chain `x` (fix round F4).

## 5. Reads outside this repo (read-only)

- `~/code/agentik-session/scripts/hygiene`, `scripts/bounded`, `tests/test_hygiene.py`, `design/conventions.md`, `LICENSE`.
- `~/code/agentik-decisions/README.md`, the section "Conventions shared with the sibling plugins" only.
- `~/code/agentik-{session,decisions,respeak,relay,agents}/plugin/.claude-plugin/plugin.json`, for the versions.

Forbidden: any transcript, any `~/.local/state` folder, the owner's ledger, any other repo, and `~/.config/agentik/hygiene-private.tsv` (the scan reads it; you never print or copy it).

## 6. Report (one table, at most five bullets, under 1,500 words)

The acceptance table with each line's actual output; the commits; each ruling taken beyond §2 in one sentence; anything left for `NICE_TO_HAVE.md`.
