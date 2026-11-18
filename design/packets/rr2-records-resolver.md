# Packet rr2-records-resolver: the records root's resolver, its cases, `agentik records`

| item | value |
|---|---|
| from | agentik-hq's brief rr2-records-resolver of 2026-11-18, R1 to R9; hq design/28 §3 items 1 to 6 and §11 (B1, B2, lead 2); level S3 |
| pin | agentik-commons main 4aa4347 (suite 0.7.34); worktree `.claude/worktrees/rr2-records-resolver`, branch `rr2-records-resolver`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; `scripts/sync` runs only on temp trees; no test reads a real repo's git config, the live home or the live state; made-up names in fixtures |
| may touch | `scripts/agentik_records.py` (new), `tests/records_cases.json` (new), `tests/test_rr2_records.py` (new), `scripts/sync`, `tests/test_sync.py`, `tests/test_ak10b_term.py` (the closing line), `plugins/suite/lib/agentik_records.py` (new, the copy), `plugins/suite/lib/agentik_suite/cli.py`, `plugins/suite/lib/agentik_suite/doctor.py`, `plugins/suite/lib/agentik_suite/messages.md`, `plugins/suite/.claude-plugin/plugin.json`, `design/voice/checked.sha256`, `tests/test_agentik_suite.py` (the fixture's working folder), `tests/test_sc5_first_screen.py` (the kept ids' pin), `tests/test_ak3d_doctor.py`, `tests/test_ak9b_plug_reader.py`, `tests/test_sc10_doctor_checks.py` (an in-process doctor's working folder alone), `GUIDE.md` (§12, new), `README.md` (the resolver's and sync's rows), `history/sittings/2026-11-18-1-rr2-records-resolver.md`, this packet |
| verify | the new and touched test files directly; `make voice` and `make check` once each, last, through the gate queue |
| acceptance | 1 to 4 below |

## 1. The finding

hq design/28: a public repo's working records may live outside its clone, named by one key in the clone's own git config, `agentik.records`. At the pin no code reads that key, commons holds no resolver, and `scripts/sync` places three files in a tool's `plugin/lib/` (`agentik_install.py`, the launcher, the door) and the `agentik_term` package; the suite has thirteen verbs and no `records`.

## 2. Rulings

- R1, the file: `scripts/agentik_records.py`, stdlib, Python 3.9; `resolve(start)` returns the `agentik.records/1` object; git runs as `git -C <start>`, the key read as `git config --local --path --get agentik.records`.
- R2, the states: `own` (no key, no declaration: `records` and `holder` the `--show-toplevel` of `start`, so a worktree answers its own top), `out` (the key resolves), `unset` (declared, no key), `broken` (the key does not resolve; never a records folder). `repo` is the main checkout through `--git-common-dir`, used by the `out` checks alone.
- R3, the checks, each its own `why`: absolute; an existing folder; outside the main checkout and every worktree, by real path; its last name the main checkout's folder name; and a holder whose tree declares `out` is `broken`.
- R4, the declaration: `suite.records: out` in `.claude/agentik/config.yaml` or `records: out` in `.hygiene-allow`, each a whole line of the file at `HEAD`, read through git; an untracked, uncommitted or local line declares nothing.
- R5, the holder: the top of the git repository whose working folder holds `records`, or none; `prefix` is `records` relative to it.
- R6, the cases: `tests/records_cases.json`, one layout a case, built under a temp folder by `tests/test_rr2_records.py`.
- R7, the sync: with `plugin/lib/`, `sync` places `plugin/lib/agentik_records.py`, listed in the sums and named in the closing line.
- R8, the suite: `agentik records [--json] [DIR]`; one doctor row, `records`; the suite's copy `plugins/suite/lib/agentik_records.py` held byte-equal by a test; messages through the catalogue and the voice check.
- R9, the guide: GUIDE §12, the key, the states and the verb. No tool is synced here.

## 3. Interfaces

- The object, in this key order: `schema` (`agentik.records/1`), `repo`, `records`, `holder`, `prefix`, `state`, `why`. Paths are real paths; `prefix` is `.` where `records` is the holder's top; a key with no value is `null`.
- `why`: `null` in `own` and `out`; `no-key` in `unset`; in `broken` one of `unread` (git cannot read the key), `relative`, `missing`, `inside`, `name`, `holder`. A tool prints its own sentence for each.
- `resolve` raises `NoRepo` where `start` is no folder, git is absent, or `start` is in no git working tree. git runs with the repository's own environment variables (`git rev-parse --local-env-vars`, `GIT_CONFIG_KEY_*`, `GIT_CONFIG_VALUE_*`) dropped, so a hook's `GIT_DIR` does not move the answer.
- `records` prints one line a key but `schema`, `none` for a null, and `why` as its sentence; `--json` the object alone; exit 0 in every state, 2 for a DIR that is no folder or in no repo, or a second word. It writes nothing.
- The doctor row, `records`, in the suite's group after the user settings: `ok` in `own` and `out`, `warn` in `unset`, `fail` in `broken`, the state's name in the detail of every state but `own`; no row where the working folder is in no repo.
- `sync`'s closing line with `plugin/lib/` adds `lib/agentik_records.py` after `lib/agentik_install.py`.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | every case of `tests/records_cases.json` (`python3 -m unittest tests.test_rr2_records -k test_cases`) | red: no `scripts/agentik_records.py` |
| 2 | R7: the placed copy byte-equal, listed, a one-byte change red under `shasum -c` (`tests/test_sync.py`); a tree with no `plugin/lib/` gets the pin's `vendored.sha256` byte for byte | seven rows, sum 61746a92 |
| 3 | `plugins/suite/bin/agentik-suite records --json` in a temp clone with no key: `own`, `records` the clone's top; in a worktree of it, that worktree's top (`-k test_launcher`) | red: no verb `records` |
| 4 | `scripts/hygiene --require-private --commits main..HEAD` exits 0; suite 0.7.35; `make check` green through the gate on the head handed back | green |
