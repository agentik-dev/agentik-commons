# The hq check: `make check` holds the records to their shape.

.PHONY: check recordlint help

help:
	@echo "make check       recordlint, then CLAUDE.md's block against DECISIONS.md"
	@echo "make recordlint  scripts/recordlint against its sha256, then HANDOFF.md and NICE_TO_HAVE.md"

# scripts/recordlint is a copy of agentik-commons' record check. Never edit it here.
recordlint:
	@shasum -a 256 -c --status scripts/recordlint.sha256 \
	  || { echo "recordlint: scripts/recordlint is not the file scripts/recordlint.sha256 names; copy it again from agentik-commons" >&2; exit 2; }
	scripts/recordlint

check: recordlint
	agentik decisions render --check
