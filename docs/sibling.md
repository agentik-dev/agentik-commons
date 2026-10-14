## Conventions shared with the sibling plugins

This plugin is one of five built to the same conventions, the agentik guide (`GUIDE.md` in agentik-commons).
`scripts/agentik` (the front door), `scripts/hygiene` (the name and path lint) and `scripts/bounded` are vendored from agentik-commons, their sha256 pinned in `scripts/vendored.sha256`, which `make check` verifies; `scripts/doclint` (charters, packets, links) is byte-identical across them, pinned by hash in the Makefile.
`scripts/hygiene` keeps only generic patterns. The private ones (a person, a private repo, a host, a domain) live outside it, in `$AGENTIK_HYGIENE_PRIVATE` or `~/.config/agentik/hygiene-private.tsv`, `group<TAB>regex` rows.
Without it the scan warns once and runs the generic groups; `--require-private` exits 2.
`scripts/bounded` holds `make check` to one run per tree, a 840 s wall, and no start above a load of 4 per core.
Each README is rendered from its source, and the sidecar `design/readme/rendered.sha256` holds the two hashes `make check` reads.

Each README follows this paragraph with its own table of the siblings it uses: `| id | range | role |`.
