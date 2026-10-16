# agentik-commons

The shared ground of the five agentik tools (session, decisions, respeak, relay and agents): the `agentik` front door, the one `agentik` marketplace that lists all five plugins, the consistency guide, and the canonical copies of the scripts each tool repo vendors.
It builds no tool: no `install` target, no plugin of its own.

## What it holds

| path | what |
|---|---|
| `bin/agentik` | the front door, POSIX `sh`: `agentik <tool> args…` execs `agentik-<tool>` from PATH; `agentik` lists the tools; exit 3 names the repo of a tool not on PATH |
| `.claude-plugin/marketplace.json` | the `agentik` marketplace: five `git-subdir` entries on `github.com/agentik-dev`, checked by `scripts/marketplace-check` |
| `GUIDE.md` | the conventions every tool repo follows: layout, naming, verbs, exit codes, README shape, install and hygiene |
| `docs/sibling.md` | the paragraph each README carries under "Conventions shared with the sibling plugins" |
| `scripts/hygiene` | the canonical hygiene scan, its `renamed` group included |
| `scripts/bounded` | the breaker `make check` runs under in each tool repo |
| `scripts/plugin-version-check` | run from a plugin repo's root: exit 1, one line per file, when `plugin/` changed after the commit that last changed `plugin.json`'s version (GUIDE §7) |
| `scripts/sync <repo>` | copies `bin/agentik`, `scripts/hygiene`, `scripts/bounded` and `scripts/plugin-version-check` into `<repo>/scripts/` and writes `scripts/vendored.sha256` |

## Make targets

- `make check`: the tests, `sh -n` and the line bound on the front door, the hygiene scan of this repo, and the marketplace check.
- `make local-marketplace`: writes the marketplace with `file://` urls (one checkout per tool under `AGENTIK_CODE`, default this repo's parent folder) into `AGENTIK_MARKETPLACE_DIR` (default `~/.local/share/agentik/marketplace`), then checks it.

## Tests

Python stdlib `unittest`, no venv: `make test` runs `python3 -m unittest discover -s tests`.

## Design of record

[design/agentik-r1.md](design/agentik-r1.md): one command surface, and this repo.

## License

MIT; see [LICENSE](LICENSE).
