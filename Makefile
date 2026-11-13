# agentik-commons: the tools' shared ground. It builds no tool; it holds one
# plugin, `suite`, in plugins/suite: the suite's default set and the
# agentik-suite command that manages it (hq design/04 sections 5 and 11).
# `make install` places that command with its own install-cli, under PREFIX
# when it is set; `setup` at the root runs its setup. `make help` lists the
# targets. No marketplace entry holds a `version`: each plugin.json is the one
# pin, so nothing compares them.

REPO := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
AGENTIK_CODE ?= $(patsubst %/,%,$(dir $(REPO)))
AGENTIK_MARKETPLACE_DIR ?= $(HOME)/.local/share/agentik/marketplace
AGENTIK_MARKETPLACE_OVERLAY ?= $(HOME)/.config/agentik/marketplace-local.json
PYTHON ?= python3
FRONT_DOOR_MAX_LINES := 100

.PHONY: check test lint hygiene recordlint marketplace-check voice voice-check local-marketplace install help

check: test lint hygiene recordlint marketplace-check voice-check

test:
	$(PYTHON) -m unittest discover -s tests

lint:
	sh -n bin/agentik
	sh -n scripts/sync
	sh -n setup
	@n=$$(wc -l < bin/agentik); [ "$$n" -lt $(FRONT_DOOR_MAX_LINES) ] || \
		{ echo "bin/agentik: $$n lines, the bound is under $(FRONT_DOOR_MAX_LINES)" >&2; exit 1; }

hygiene:
	scripts/hygiene

# HANDOFF.md and NICE_TO_HAVE.md held to their tables (hq design/05 §4); a file
# without its canonical header, or absent, prints skip and passes.
recordlint:
	scripts/recordlint

marketplace-check:
	scripts/marketplace-check

# The suite command's catalogue against its voice (packet ak1a R5): `voice` runs the voice
# scanner (scripts/voice says where it finds one) and, on its pass, writes
# design/voice/checked.sha256; it is not in `check`, which runs `voice-check`, a stdlib compare
# of the catalogue with that line.
voice:
	$(PYTHON) scripts/voice

voice-check:
	$(PYTHON) scripts/voice --check

# The same marketplace with file:// urls, one checkout per tool under
# $(AGENTIK_CODE), plus the entries of the owner's overlay, kept outside every
# repo, for a plugin whose repo is not public (absent: none), written into
# $(AGENTIK_MARKETPLACE_DIR) (agentik-r1 D1).
local-marketplace:
	$(PYTHON) scripts/local-marketplace .claude-plugin/marketplace.json "$(abspath $(AGENTIK_CODE))" \
		"$(AGENTIK_MARKETPLACE_OVERLAY)" "$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json"
	scripts/marketplace-check --local "$(AGENTIK_MARKETPLACE_DIR)/.claude-plugin/marketplace.json"

# The suite's command on the terminal's PATH, under PREFIX when it is set, else ~/.local
# (packet ak2b R7). It writes the real HOME, so no test or gate runs it; one runs `make -n`.
install:
	plugins/suite/bin/agentik-suite install-cli$(if $(PREFIX), --prefix "$(PREFIX)")

help:
	@echo 'make check              test, lint, hygiene, recordlint, marketplace-check and voice-check'
	@echo 'make test               the stdlib unittest suite'
	@echo 'make lint               sh -n on the front door, sync and setup, the front door line bound'
	@echo 'make hygiene            the hygiene scan of this repo'
	@echo 'make recordlint         HANDOFF.md and NICE_TO_HAVE.md against their tables'
	@echo 'make marketplace-check  the shape of .claude-plugin/marketplace.json'
	@echo 'make voice              the suite command'"'"'s catalogue through the voice scanner, then its sidecar'
	@echo 'make voice-check        the catalogue against design/voice/checked.sha256 (in check)'
	@echo 'make local-marketplace  the marketplace with file:// urls into AGENTIK_MARKETPLACE_DIR,'
	@echo '                        plus the entries of AGENTIK_MARKETPLACE_OVERLAY when present'
	@echo 'make install            the agentik-suite command and the agentik door, by its install-cli,'
	@echo '                        under PREFIX when set, else ~/.local'
