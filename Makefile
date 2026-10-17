# agentik-commons: the tools' shared ground. It builds no tool, so it has no
# install target and no plugin of its own (agentik-r1 A9). `make help` lists the
# targets; `make check` compares the marketplace's versions only when every
# tool's checkout is present under $(AGENTIK_CODE), so a clone of commons alone
# stays green.

REPO := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
AGENTIK_CODE ?= $(patsubst %/,%,$(dir $(REPO)))
AGENTIK_MARKETPLACE_DIR ?= $(HOME)/.local/share/agentik/marketplace
AGENTIK_MARKETPLACE_OVERLAY ?= $(HOME)/.config/agentik/marketplace-local.json
PYTHON ?= python3
FRONT_DOOR_MAX_LINES := 100

.PHONY: check test lint hygiene marketplace-check versions local-marketplace help

check: test lint hygiene marketplace-check
	AGENTIK_CODE="$(AGENTIK_CODE)" scripts/marketplace-versions --if-complete

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

# Each marketplace line against $(AGENTIK_CODE)/agentik-<name>'s plugin.json; an
# absent checkout is skipped with a note. No network.
versions:
	AGENTIK_CODE="$(AGENTIK_CODE)" scripts/marketplace-versions

# The same marketplace with file:// urls, one checkout per tool under
# $(AGENTIK_CODE), plus the entries of the owner's overlay, kept outside every
# repo, for a plugin whose repo is not public (absent: none), written into
# $(AGENTIK_MARKETPLACE_DIR) (agentik-r1 D1).
local-marketplace:
	$(PYTHON) scripts/local-marketplace .claude-plugin/marketplace.json "$(abspath $(AGENTIK_CODE))" \
		"$(AGENTIK_MARKETPLACE_OVERLAY)" "$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json"
	scripts/marketplace-check --local "$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json"

help:
	@echo 'make check              test, lint, hygiene and marketplace-check, then the versions'
	@echo '                        compare, but only when every checkout is present under'
	@echo '                        AGENTIK_CODE (else one note, and check stays green)'
	@echo 'make test               the stdlib unittest suite'
	@echo 'make lint               sh -n on the front door and sync, the front door line bound'
	@echo 'make hygiene            the hygiene scan of this repo'
	@echo 'make marketplace-check  the shape of .claude-plugin/marketplace.json'
	@echo 'make versions           each marketplace line against its checkout plugin.json under'
	@echo '                        AGENTIK_CODE (default this repo parent folder); an absent'
	@echo '                        checkout is skipped with a note'
	@echo 'make local-marketplace  the marketplace with file:// urls into AGENTIK_MARKETPLACE_DIR,'
	@echo '                        plus the entries of AGENTIK_MARKETPLACE_OVERLAY when present'
