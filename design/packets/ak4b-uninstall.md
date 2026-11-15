# Packet ak4b-uninstall: `uninstall` in the install module, the reverse of `install-cli`

| item | value |
|---|---|
| from | agentik-hq's brief ak4b-uninstall of 2026-11-14, R1 to R9, acceptance 1 to 10; level S3 |
| pin | main at 1f043e8 (suite 0.7.14, ak9d-contract-guide landed); worktree `.claude/worktrees/ak4b-uninstall`, branch `ak4b-uninstall`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge, install or sync; no bare `make`; no relay verb or binary; no `claude` started; `uninstall` is never called with the live home or `~/.local` as its prefix, `dry` included: every test's prefix, home and state folder lie under its temp folder, asserted before the call; no verb, flag or message; made-up names |
| may touch | `scripts/agentik_install.py`; `plugins/suite/lib/agentik_install.py` (a byte-equal copy); `plugins/suite/.claude-plugin/plugin.json` (0.7.15, alone, last under `plugins/`); `tests/test_ak4b_uninstall.py`; `GUIDE.md` (§10's `install-cli` paragraph alone); this packet; `history/sittings/2026-11-14-16.md` |
| verify | `make check` once, last, through the gate queue, `--strict` |
| acceptance | 1 to 10 below |
| budget | a commit per ruling group by explicit path, this packet first; about 90 tool calls; `claude-opus-5-5` |

## 1. What it is for (the brief)

The owner, 2026-11-12: "how I configure my work computer with agentik plugins, and in general, how others might try out what I've written". The design:

> Remove is setup's plan reversed: `claude plugin uninstall`, then the launcher, its links and its frozen trees, by a new `uninstall` in the canonical install module (only a file that reads as the launcher `install-cli` wrote is removed).

A person who tried the tools must be able to take them off again and trust what went. The function deletes under a person's home, so its whole rule is: remove a thing only where the code can show `install-cli` wrote it, say what was kept and why, and on any doubt remove nothing. This row is that function and nothing above it; the verb `agentik remove` is the next row's.

## 2. Rulings (the brief's, in short)

- R1: `uninstall(tool_name, prefix=None, door=False, dry=False, spare=())`, the suite's copy byte-equal. `tool_name` of `names()`'s form, else `ValueError` before any read of the disk; `prefix` defaults as `install_cli`'s. It returns rows `(path, what, fate)` in the order acted on and prints nothing; `what` one of `launcher`, `link`, `tree`, `share`, `marker`, `door`; `fate` `removed`, `would remove` or `kept: <why>`. A second call returns `[]`.
- R2, the hold: under the share's lock, a process list that cannot be read, or a process that names a tree of the share (`named`), keeps every row as `kept: held, <what is live>`. A pid in `spare` is passed over.
- R3, the launcher: a regular file, no link, under 64 KiB, its second line the template's for the name, its `TREE=` under `<prefix>/share/<tool_name>/` by real paths. Else `kept: not the launcher install-cli wrote`, and every other row of the tool is kept with that reason.
- R4, the links: a symlink directly in `<prefix>/bin` whose text is exactly the tool's name, or whose target resolves inside the share; no other link, and none followed.
- R5, the share: a real directory whose real path is `<prefix>/share`'s plus the name. Inside: each tree (`_freeze`'s name), each `.tmp-*`, then `.lock`, by a walk that follows no link; any other entry `kept: not install-cli's`, and the directory stays. The directory goes only when empty.
- R6, the marker: `install-needed` on `_clear_marker`'s own rule, the default prefix alone.
- R7, the door, with `door=True` alone: a regular file, no link, its second line opening `# agentik: the front door`, a `VERSION=` line, and no other file in the bin that passes R3's first three tests for its own name.
- R8, the bounds: each removal is asserted inside `<prefix>/bin`, `<prefix>/share/<tool_name>` or R6's file; `os.unlink`, `os.rmdir` and a walk of its own, no shell; a prefix whose real path is `/` or the home folder's parent is a `ValueError`; `dry` reads and removes nothing.
- R9: `GUIDE.md` §10's `install-cli` paragraph says what `uninstall` takes back and its rule; the suite takes 0.7.15, alone, in the last commit under `plugins/`.

## 3. Interfaces

`uninstall(tool_name, prefix=None, door=False, dry=False, spare=())` returns `[(path, what, fate), ...]`. The process list is read by `processes(PS)`, where `PS` is a module name for `ps` (default `"ps"`) that a test points at a stub; a line of its output opens with the pid. The second line of a launcher `install-cli` wrote has had one form in this repo's history (`git log -S'launcher, written by'`: ad54b27, adca15d, 56d6b3c, each the same line): ``# <tool_name> launcher, written by `<tool_name> install-cli` (hq design/04 §2, §3).``

## 4. At the pin

Measured at 1f043e8: `grep -c 'def uninstall' scripts/agentik_install.py` 0; `tests/test_ak4b_uninstall.py` absent; `python3 -m unittest tests.test_agentik_install` OK; `test_copies_are_byte_equal` OK; `scripts/hygiene` and `scripts/hygiene --require-private --commits main..HEAD` exit 0; the suite at 0.7.14.

## 5. Acceptance

Each line is a test of `python3 -m unittest tests.test_ak4b_uninstall`, on `tests/test_agentik_install.py`'s `Base` (a real plugin, a real `install-cli` into a temp prefix) and a stub `ps`. At the pin every line is red: the module has no `uninstall`.

| # | line |
|---|---|
| 1 | install, then `uninstall(name, prefix)`: the launcher, the trees, `.lock` and the share are gone; `<prefix>/bin` holds the door alone; the rows name each path once; a second call returns `[]` |
| 2 | `dry=True`: the same rows with `would remove`; the prefix is byte for byte what it was |
| 3 | an old-name link whose text is the tool's name, and a link into the share: removed; a link to another program and a link whose text is another tool's name: there after |
| 4 | a launcher with `VERSION=` and `TREE=` and no second line of the template; one with the line and a `TREE=` outside the share; one that is a symlink to a real launcher; one of 70 KiB: each `kept`, and the share and its trees there after |
| 5 | the share a symlink to a folder elsewhere: nothing under the target removed; a file `notes.txt` in the share: it and the directory stay, the trees go |
| 6 | a process whose environment or argv names a tree (the stub `ps`): every row `kept: held`, nothing removed; the same pid in `spare`: removed; a `ps` that fails: held |
| 7 | `door=True` alone in the bin: the door goes; beside another tool's installed launcher: the door is `kept`; a door that is a link, and a hand-written `agentik` with no second line: `kept` |
| 8 | `tool_name` `../x`, `a/b`, empty: `ValueError`, the disk unread; a prefix of `/`: `ValueError` |
| 9 | a prefix whose path holds a space; two tools installed, one uninstalled: the other's launcher, trees and share untouched, and it still runs `--version` |
| 10 | `test_copies_are_byte_equal` green; `tests/test_agentik_install.py` unedited and green; both hygiene scans exit 0; `make check` once, last, through the gate queue, green |

## 6. Choices

Listed in the charter's handover as they are made.
