# agentik-commons

The shared ground of the five agentik tools (session, decisions, respeak, relay and agents): the `agentik` front door, the one `agentik` marketplace that lists the five plugins and `suite`, the consistency guide, and the canonical copies of the scripts each tool repo vendors.
A fresh Mac installs the suite in one line (hq design/04 §5):

```sh
claude plugin marketplace add agentik-dev/agentik-commons && claude plugin install suite@agentik
```

`suite` is this repo's one plugin, manifest-only: `plugins/suite` holds no code, only `dependencies` on session, decisions and agents, which Claude Code installs and enables with it. Updates stay `claude plugin marketplace update agentik && claude plugin update <name>@agentik`.
It builds no tool: no `install` target.

## What it holds

| path | what |
|---|---|
| `bin/agentik` | the front door, POSIX `sh`: `agentik <tool> args…` execs `agentik-<tool>` from PATH; `agentik` lists the tools; exit 3 names the repo of a tool not on PATH |
| `.claude-plugin/marketplace.json` | the `agentik` marketplace as published: six `git-subdir` entries on `github.com/agentik-dev`, public repos only, the five tools' at `plugin` and `suite`'s on this repo's own url at `plugins/suite`, checked by `scripts/marketplace-check`; a plugin whose repo is not public reaches the owner's machine through the local file's overlay only |
| `plugins/suite` | the manifest-only `suite` plugin: `plugin.json` and its `dependencies`, nothing else |
| `GUIDE.md` | the conventions every tool repo follows: layout, naming, verbs, exit codes, README shape, install and hygiene |
| `docs/sibling.md` | the paragraph each README carries under "Conventions shared with the sibling plugins" |
| `scripts/hygiene` | the canonical hygiene scan, its `renamed` group included |
| `scripts/bounded` | the breaker `make check` runs under in each tool repo |
| `scripts/plugin-version-check` | run from a plugin repo's root: exit 1, one line per file, when `plugin/` changed after the commit that last changed `plugin.json`'s version (GUIDE §7) |
| `scripts/suite-probe` | run by hand, never by `make check`: clones this HEAD and the three tools' mains into a temp HOME, runs `claude plugin marketplace add` and `install suite@agentik` there with no model reached, reads `installed_plugins.json`, the exec bits and each tool's bare commands against the installed copies, then whether `update` installs a bump with and without the entry's `version` |
| `scripts/marketplace-versions` | each marketplace line against its checkout's `plugin/.claude-plugin/plugin.json` under `AGENTIK_CODE`, suite's against `plugins/suite`; exit 1, one line per entry that trails, leads or differs, or whose checkout has no readable version; no network |
| `scripts/agentik_install.py` | the canonical `install-cli`: freeze, launcher, prune and forward refresh, generic by name, stdlib at Python 3.9 (GUIDE §10) |
| `scripts/plugin-launcher` | the canonical launcher a plugin keeps in `plugin/bin/agentik-<tool>`; its names come from `plugin/lib/agentik-tool.conf` (GUIDE §10) |
| `scripts/sync <repo>` | copies `bin/agentik`, `scripts/hygiene`, `scripts/bounded` and `scripts/plugin-version-check` into `<repo>/scripts/` and writes `scripts/vendored.sha256`; in a repo with a `plugin/lib/`, also the two above and the door, listed there too |

## Make targets

- `make check`: the tests, `sh -n` and the line bound on the front door, the hygiene scan of this repo, and the marketplace check; then the versions compare, only when every tool's checkout is present under `AGENTIK_CODE`, so a clone of this repo alone stays green.
- `make versions`: each marketplace line against its checkout's `plugin.json` (one checkout per tool under `AGENTIK_CODE`, default this repo's parent folder); an absent checkout is skipped with a note.
- `make help`: the targets, one line each.
- `make local-marketplace`: writes the marketplace with `file://` urls (one checkout per tool under `AGENTIK_CODE`, default this repo's parent folder) into `AGENTIK_MARKETPLACE_DIR` (default `~/.local/share/agentik/marketplace`), then checks it with `marketplace-check --local`. The published file names public repos only; the local file leaves out `suite` (this Mac installs the tools by name) and adds, after the five, the entries of the overlay `AGENTIK_MARKETPLACE_OVERLAY` (default `~/.config/agentik/marketplace-local.json`, kept outside every repo), a JSON object whose `plugins` are in the published form, for a plugin whose repo is not public. An absent overlay adds nothing; one that cannot be read, is not JSON or has no `plugins` list fails the target, which then writes nothing. `scripts/local-marketplace` does the merge.

## Tests

Python stdlib `unittest`, no venv: `make test` runs `python3 -m unittest discover -s tests`.

## Design of record

[design/agentik-r1.md](design/agentik-r1.md): one command surface, and this repo.

## License

MIT; see [LICENSE](LICENSE).
