# agentik-commons: the tools' shared ground. It builds no tool, so it has no
# install target and no plugin of its own (agentik-r1 A9).

REPO := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
AGENTIK_CODE ?= $(patsubst %/,%,$(dir $(REPO)))
AGENTIK_MARKETPLACE_DIR ?= $(HOME)/.local/share/agentik/marketplace
PYTHON ?= python3
FRONT_DOOR_MAX_LINES := 100

.PHONY: check test lint hygiene marketplace-check local-marketplace

check: test lint hygiene marketplace-check

test:
	$(PYTHON) -m unittest discover -s tests

lint:
	sh -n bin/agentik
	sh -n scripts/sync
	@n=$$(wc -l < bin/agentik); [ "$$n" -lt $(FRONT_DOOR_MAX_LINES) ] || \
		{ echo "bin/agentik: $$n lines, the bound is under $(FRONT_DOOR_MAX_LINES)" >&2; exit 1; }

hygiene:
	scripts/hygiene

marketplace-check:
	scripts/marketplace-check

# The same marketplace with file:// urls, one checkout per tool under
# $(AGENTIK_CODE), written into $(AGENTIK_MARKETPLACE_DIR) (agentik-r1 D1).
local-marketplace:
	@mkdir -p "$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin"
	$(PYTHON) -c 'import json, pathlib, sys; d = json.load(open(sys.argv[1])); \
	[p["source"].update(url=pathlib.Path(sys.argv[2], "agentik-" + p["name"]).as_uri()) \
	 for p in d["plugins"]]; \
	open(sys.argv[3], "w").write(json.dumps(d, indent=2) + "\n")' \
		.claude-plugin/marketplace.json "$(abspath $(AGENTIK_CODE))" \
		"$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json"
	scripts/marketplace-check --local "$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json"
