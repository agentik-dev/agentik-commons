# Packet M1: no marketplace entry holds a `version`; `plugin.json` is the one pin

| item | value |
|---|---|
| from | agentik-commons NICE n7 (S4) and n1 (S3); the suite review of 2026-11-10, F1; probes beside this packet in `PACKET-2026-11-10-commons-m1-probes/` |
| pin | agentik-commons main 5689f3b; worktree `.claude/worktrees/m1-marketplace-versions`, branch `m1-marketplace-versions` |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no `relay`/`agentik relay` `run`, `plan`, `gate`, `stop`, `kill`, `clean`, `resume`, nothing under `~/.local/state/agent-relay`; no `claude plugin` command run for real: `scripts/suite-probe` is edited, never run |
| may touch | `.claude-plugin/marketplace.json`; `scripts/marketplace-check`, `scripts/local-marketplace`, `scripts/suite-probe`; `scripts/marketplace-versions` and `tests/test_marketplace_versions.py` (removed); `tests/test_marketplace.py`; `Makefile`; `README.md`; `GUIDE.md` (§2's entry shape, §7's last clause); `NICE_TO_HAVE.md`; this packet as `design/packets/m1-marketplace-versions.md`; `history/sittings/*.md` |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash; read the job's code from its line |
| acceptance | `python3 -m unittest tests.test_marketplace`, PATH's `python3` the 3.9.6 then a 3.12: OK with M1 to M7 in it (5689f3b with the tests alone: 7 of 7 fail, `failures=10`, under 3.9.6 and 3.14.7); `scripts/marketplace-check` exit 0; `grep -rn -E 'marketplace-versions|make versions' Makefile README.md GUIDE.md scripts tests` no line; `grep -c -E '^\| n(1|7) \|' NICE_TO_HAVE.md` 0; `scripts/hygiene` and `scripts/recordlint` exit 0; verify green |
| budget | a commit per group by explicit path, the packet first; `scripts/hygiene` green before every commit; stop at 60 tool calls or 120k context, with a resume line. `claude-opus-5-5` |

## 1. What the source says (5689f3b)

- **The lines.** Each of the six entries holds `version`. Session's reads alpha.45 against its `plugin.json`'s alpha.65, decisions' 0.11.0 against 0.18.2.
- **The shape check.** `scripts/marketplace-check:120-122` wants a semver `version` on every entry, in both modes (`:13`, `:23` say so).
- **The local file.** `scripts/local-marketplace:64-80` copies each entry through, the overlay's too.
- **The one reader.** `scripts/marketplace-versions` (145 lines); `Makefile:18` runs it `--if-complete` as `check`'s last line, `:42-43` as `versions`. A worktree's parent holds no checkout, so every gate printed `5 of 6 checkouts absent ...; not compared`; on main it exits 1.
- **The probe.** `scripts/suite-probe:267-293` asks the version question in two cases.
- **Nothing installs from the line**, three ways:
  1. Claude Code's manifest reference, "Metadata precedence" (https://code.claude.com/docs/en/plugins-reference, read 2026-11-10): "**`version`**: the manifest's `version` overrides the entry's". Under `version`: "Setting it pins the plugin to that version until you change it". Every tool's `plugin.json` holds one, suite's too.
  2. c2's probe, charter 2026-11-01-2: "entry version left at 1.5.1, update installs 1.5.2; removed, installs 1.5.3".
  3. The owner's machine, 2026-11-10: the marketplace file Claude Code reads, written 2026-10-17, holds session alpha.18, decisions 0.9.0, agents 1.2.2; `installed_plugins.json` holds alpha.65, 0.18.2, 1.5.3.

## 2. Rulings

1. No entry of `.claude-plugin/marketplace.json` holds `version`. `description` stays.
2. `marketplace-check`, both modes: no entry needs a `version`, and an entry holding the key is one problem line, `plugins[i] (name): version is set; plugin.json holds the one version`. Its docstring's sentence becomes "Every `version` is plugin.json's: an entry holding one is a problem line."
3. `local-marketplace` drops a `version` key from every entry it writes, the overlay's included, so an older overlay still passes `--local` unedited.
4. `scripts/marketplace-versions`, its test, the `versions` target, `check`'s last line, and the Makefile's header and help lines for them go. `check` is `test lint hygiene recordlint marketplace-check`.
5. `suite-probe`'s version question keeps one case: the bump, the two updates, and the bump is installed or the probe fails (`expect`, not a note); its docstring says so. Edited, never run.
6. README: the `scripts/marketplace-versions` row and the `make versions` bullet go; the `make check` bullet ends at the marketplace check. GUIDE §2 reads `description}]`; in §7 the clause ", and commons' `make versions` shows a marketplace line that trails it" goes.
7. NICE rows n1 and n7 leave, built; the frozen archive stays.

## 3. Tests

`tests/test_marketplace.py` takes the probe's `test_marketplace_m1.py`:

| M | test | 5689f3b |
|---|---|---|
| 1 | no committed entry holds `version` | red |
| 2 | the six without a `version`: exit 0, `6 plugins, valid` | red |
| 3 | a `version` on session's entry, then on suite's: exit 1, one line, ruling 2's | red |
| 4 | `--local`: the five without one exit 0; an extra entry with one, that one line | red |
| 5 | `local-marketplace` with an overlay entry holding `version`: exit 0, no entry written holds one, `--local` passes | red |
| 6 | the script, its test, the target and the `.PHONY` word are gone | red |
| 7 | README and GUIDE name neither; GUIDE §2's shape; the probe has no "left at the"; ruling 2's docstring | red |

Edited as the rulings make them: `:75-76` (suite's `version="0.1"`) and `:118` and `:165` expect ruling 2's line; `:119`'s `noversion` case goes, it is the valid shape; the fixtures at `:152`, `:219`, `:254`, `:274` lose `version`. The suite: 173, less the 12 of `test_marketplace_versions.py`, plus 7, is 168. No prototype: green is the builder's.

## 4. What changes outside this packet

No tool repo reads the line: `scripts/plugin-version-check` reads `plugin.json`'s history only and never names the marketplace; the doctors read the installed version. No vendored file changes, so no sync row follows.

The hq half, the coordinator's small change after this lands:

- `scripts/suite`: `:4` and `:511-513`, the `--marketplace` flag; `:10` and `:505`, the docstring and help words; `:36` `COLUMNS`, `:37` `MARKS` (`marketplace_trails`), `:43` `CUT_TIERS`; `:129-145`, `load_marketplace`; `:296-300`, the cell and its mark; `:331`, the tuple; `:462-466`, the load.
- `tests/test_suite.py`: `:4`, `:64-66`, `:95-98`, `:127`, `:171`, `:184-186`, `:194`, `:202`, `:212`, `:270`, `:297`.
- `CLAUDE.md:11`, step 8: "a plugin bumps `plugin.json` and the marketplace line in commons" becomes "a plugin bumps `plugin.json`".

## 5. Ledger, NICE, forks

- Commons has no ledger. hq entry 6 holds: the one marketplace stays in commons, a plugin repo keeps none.
- hq design/04 §6, the design of record, verbatim: "| marketplace `version`, `marketplace-versions` | If c2's probe shows `claude plugin update` finds a bump with no entry version, drop the lines and the script; if not, both stay. |" and "five pins ... | **One**, `plugin.json`." §1's second proof meets the condition.
- GUIDE.md:32 (§2), verbatim: "`plugins: [{name, source: {source: "git-subdir", url, path: "plugin"}, description, version}]`". GUIDE.md:61 (§7), verbatim: "`scripts/plugin-version-check` fails when a file under `plugin/` changed after the commit that last changed the version (a bump not yet committed passes), and commons' `make versions` shows a marketplace line that trails it."
- Forks ruled here, each reversible: refuse the key, not tolerate it (2); the script drops an overlay's key, not its owner (3); the probe keeps one case (5). Any other fork stops the build with one line.

## 6. Forbidden reads and report

The owner's overlay under `~/.config/agentik/`, `~/.claude/plugins`, transcripts, `~/.local/state`. Six lines: head sha, gate id and code, M1 to M7, the suite's count, choices, leftovers.
