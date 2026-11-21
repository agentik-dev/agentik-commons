# Packet ak10c5-table-gone: the suite asks each tool for what the fallback table held, and the table goes

| item | value |
|---|---|
| from | agentik-hq's brief ak10c5-table-gone of 2026-11-21, on the parent row's eight rulings (the coordinating repo's design of the `agentik` command, P11: the table goes once every tool says what it has); level S3 |
| pin | agentik-commons main 65e15b8, the merge of rr7-way-in, with hn1-help-next's merge behind it; worktree `.claude/worktrees/ak10c5-table-gone`, branch `ak10c5-table-gone`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make`; no relay verb or binary; no `claude` process, no agent; no test reads the live home or state; made-up names in fixtures; setup, update and remove only with `--dry-run` against this Mac |
| may touch | `plugins/suite/lib/agentik_suite/{tools,plan,cli,update,status,status_read,status_screen,inbox,remove,config,doctor,gather}.py`, `plugins/suite/lib/agentik_suite/messages.md`, `plugins/suite/lib/public.json`, `plugins/suite/lib/fallback.json` (removed), `GUIDE.md` §11, `README.md` (one line), `.hygiene-allow`, `NICE_TO_HAVE.md` (n249), the tests that pin the table, `tests/test_ak10c5_table_gone.py`, this packet, `history/sittings/*.md` |
| verify | `python3 -m unittest` of the touched tests directly; `scripts/hygiene --require-private --commits main..HEAD`; `make check` once, last, through the gate queue |
| acceptance | 1 to 10 below |

## 1. The finding

The owner's words (2026-11-20): "continue with the charter", which orders this row. The design is the suite's own: a tool says what it has, and the suite's table of what an old tool would have said goes once every tool says it. At the pin all five tools answer `describe` with every read the table held (session's `charter`, decisions' `rows` with `wall_s` 6, relay's `run` with `wall_s` 2.5), yet `plugins/suite/lib/fallback.json` still decides status, inbox, the update hold, setup's needs and pages, remove's keep line and config's silent card, and a tool the table names is never asked `describe`.

## 2. Rulings

- R1: status reads, inbox reads, the hold's reads and a tool's user file come from `describe` and `describe config` alone; the rule that a table tool is never asked `describe` goes from the code, GUIDE §11.1, §11.3 and §11.6, and the docstrings.
- R2: a described read keeps its `wall_s` (built at hn1-help-next); with the table gone it is the only wall beside 1 s.
- R4: `public.json` gains `needs` (`{tool: [word]}`) and `own_command` (`[tool]`); `tools.known` reads its `tools` less the suite's own row; a tool's page is `https://github.com/<repo>#install` for a name `own_command` lists. Setup reads a tool's needs from its describe's `needs` rows where a file runs and answers (a row's `name`, any case, a word of `plan.NEEDS`, and `optional` not true), else public.json's words. `gather.load_public` takes the two keys and returns what it did.
- R5: `update.reader(answers, read)` finds the `run` and `unattended` tools from the counted describes of every known tool whose file runs, the cache first, before any write. A tool whose file runs and gives no answer holds nothing, and a text update prints one line, `update.unasked`, on stderr, naming only the tools `public.json` lists (build 2, fork 2); a tool it does not list is named nowhere; no line when every listed tool answered.
- R6: `remove` asks each tool's config read in its scope and keeps the `user` layer's file; the `--all` guard holds those files; no answer, no keep line for a file, and the guard on the two config folders stands.
- R7: a tool with a file whose describe does not count gets one doctor check `describe`, `warn`, remedy `agentik update <tool>` as the door says it. `config`'s table block (title, description, run, user file, needs; JSON `table` and `description`) goes.
- R8: `fallback.json` and `tools.fallback` go; each test that held a made-up tool known, needy or paged through the table holds it through a copy's `public.json`; a screen pinned through the table is re-based on a fake tool's `describe`. Its `.hygiene-allow` row, README's line and NICE n249's mention follow.
- R9: no new verb, flag or key on any screen a person reads, save the one stderr line and the one doctor check; `agentik.describe/1` stays. With the table gone, a read a tool's describe names that the suite does not draw (session's `meter`, a second tool's `gate`) is in `--json`'s `sources` as `not drawn`; the text screen lists it only for a tool `public.json` does not name, as the pin did for a tool outside the table (build 2, fork 1: `status_screen.foot(..., named)`).

## 3. Interfaces

- `tools.public(lib)`, `tools.page(lib, name)`, `tools.answered(env, rows, deadline=None, read=False)` giving `(answers, configs, silent)`, `tools.user_layer(cfg)`; `plan.needs_of(answer, words)`; `update.asked(cmd)`, `update.holding(cmd, told=None)`; `status_screen.foot(t, obj, slots, named=())` and `draw(t, obj, slots, named=())`, `named` the tools `public.json` names.
- Messages: `update.unasked`, `doctor.tool.nodescribe` added; `config.table.*` and `config.label.{run,file,needs}` removed.

## 4. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | the su2 screen fixtures and inbox's test_16 give the pin's screen from `describe` | from the table |
| 2 | `-k test_a2_a_slow_rows_read_is_drawn`: a `rows` read of 3.8 s with `wall_s` 6, drawn | hn1's test, kept |
| 3 | `-k test_a3`, `-k test_fork2`: held during a live unattended run and a live relay run, each found by `describe`; a silent tool: one `update.unasked` line, no hold | from the table |
| 4 | `-k test_a4`: the keep line from `describe config`'s user layer; with no answer the guard's refusal | from the table |
| 5 | `-k test_a5`: doctor's `describe` warn row; status and inbox show no part for it, exit 0 | no row |
| 6 | `-k test_a6`: setup's plan of an uninstalled relay and respeak: `Go`, the page, `PyYAML`, from `public.json` | from the table |
| 7 | `grep -rn fallback plugins scripts tests GUIDE.md README.md`: no reader, no rule | 40-odd lines |
| 8 | not a test: `status`, `inbox`, `doctor` tails and `config session \| head` against this Mac, at the pin and now | the pin's, in the record |
| 9 | every test of the pin that does not pin the table passes unchanged | green at 65e15b8 |
| 10 | `scripts/hygiene --require-private --commits main..HEAD` exit 0; `make check` through the gate queue | green at 65e15b8 |
