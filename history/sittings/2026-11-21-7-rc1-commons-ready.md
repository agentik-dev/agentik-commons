# Sitting 2026-11-21-7-rc1-commons-ready: row rc1-commons-ready, build 1 (builder)

| item | value |
|---|---|
| goal | rehearse commons' whole `make check` in a scratch clone with its records removed and `records: out` declared, once with no key and once with the key set; mend in tests any red that is this repo's |
| budget | Opus; about 90 tool calls; past 80% land the act in flight and hand back |
| pin | main 3567092 (suite 0.7.42); nothing linked from main |
| wall | this worktree, a scratch clone and the holder's copy in a scratch folder outside every checkout; no push, amend, rebase, merge; no bare `make`; no relay verb; nothing under `plugins/` |
| verify | the packet's verify row; `make check` once, last, through the gate queue |

## Done-ness

| act | done-ness |
|---|---|
| 0 the packet and this charter | done |
| 1 the scratch clone and the holder's copy | done; at 2cd5fc3, 189 record paths removed (`history/` 109, `design/packets/` 79, `NICE_TO_HAVE.md`), the copy a scratch repo `holder/repos/agentik-commons/` |
| 2 R2, the rehearsal with no key | done; `state: unset`; the check green, 1436 tests OK, `records` 0 hits |
| 3 R3, the rehearsal with the key set | done; `state: out`; the check green, 1436 tests OK, `records` 0 hits |
| 4 R4, the reds mended in tests | done; nothing turned red |
| 5 the gate in this worktree | queued on the head that carries this charter |

## Next act

None but the gate: `make check` in this worktree on the head that carries this charter.

## Handover

- choice: the holder's copy is a scratch git repository with the copy committed under `repos/agentik-commons/`, so `agentik records` names a holder as in the owner's clone. Consumer: review.
- choice: R3 sets the key in R2's clone rather than a fresh one, since R2 left only ignored `__pycache__/` folders. Consumer: review.

## Exit

Build 1: every act built and committed; the gate's result on this head is the hand-back's.
