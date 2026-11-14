# Messages

Each item below is one message the command prints, by its id; the writer in `term.py` prints it.

## Help

- `help.title`: `{tool}` `{version}` manages the agentik suite's default set of plugins.
- `help.usage`: usage: `{prog}` <verb> [<name>...] [flags]
- `help.verbs`: verbs
- `help.flags`: flags
- `help.path`: agentik commands on PATH
- `help.path.none`: No agentik command is on PATH yet.
- `hint.help`: next: `{setup}`
- `hint.help.done`: next: `{doctor}`
- `hint.verb`: next: `{help}` lists every verb and the agentik commands on PATH.
- `verb.help`: List the verbs, the flags and the agentik commands on PATH.
- `verb.version`: Print the suite's version.
- `verb.setup`: Set up the suite: run each step's line in order, or show the plan with --dry-run.
- `verb.config`: Show each tool's settings, then one tool's, then one setting and how to change it.
- `verb.describe`: Print the suite's own answer, in JSON, for other tools to read.
- `verb.status`: Name each declared watcher that is not running. This version only checks, so pass --check.
- `verb.install_cli`: Place the suite's command and the agentik door on the terminal's PATH.
- `verb.doctor`: Check this machine in one read: the door, the settings file, the setup plan and each tool's own doctor.
- `usage.help`: usage: `{help}` [<verb>] [flags]
- `usage.version`: usage: `{prog}` version [flags]
- `usage.setup`: usage: `{setup}` [<plugin>...] [flags]
- `usage.config`: usage: `{config}` [<tool>[.<key>]] [flags]
- `usage.describe`: usage: `{describe}` [config [<key>]] --json
- `usage.status`: usage: `{status}` --check [flags]
- `usage.install_cli`: usage: `{install}` [--prefix <dir>] [flags]
- `usage.doctor`: usage: `{doctor}` [flags]
- `flag.json`: Print one JSON object on stdout, and nothing else there.
- `flag.quiet`: Print no hints and no progress.
- `flag.no_color`: Print no colour, on a terminal too.
- `flag.help`: Show the usage and the flags.
- `flag.dry_run`: Show the plan, and write nothing.
- `flag.yes`: Run setup's lines without asking first.
- `flag.changed`: List every setting that differs from its default.
- `flag.user_files`: Print the path of each user file that travels, one a line.
- `flag.all`: Print every check, the ok ones too.
- `flag.check`: Check each watcher the user file declares, and print a line for each one not running.
- `flag.prefix`: Place the command under this folder's bin, not under ~/.local.

## Version

- `version.line`: `{tool}` `{version}`

## Install

- `install.done`: Placed `{launcher}` at version `{version}`, running the code frozen at `{tree}`.
- `install.dry`: Would place `{launcher}` at version `{version}`. Nothing is written.
- `install.door.keep`: The door `{door}` is at this version or newer, so it stays as it is.
- `install.door.link`: The door `{door}` is a link, so it stays as it is.
- `install.door.unversioned`: The door `{door}` holds no version to compare, so it stays as it is.
- `install.pruned`: `{line}`
- `hint.install.path`: next: add `{line}` to your shell profile, then open a new terminal.
- `err.install.prefix`: --prefix needs a folder after it, and got none. Run `{install}` --prefix <folder>, or leave it out for ~/.local.
- `err.install`: install-cli stopped: `{why}`. Mend that, then run `{install}` again.

## Errors

- `err.verb.near`: `{word}` is not a verb; the nearest is `{near}`. Run `{prog}` --help for the list.
- `err.verb`: `{word}` is not a verb. Run `{prog}` --help for the list.
- `err.verb.plugin`: `{word}` is a plugin with no command here. Run `{setup}` --dry-run `{word}` for the steps.
- `err.flag.near`: `{flag}` is not a flag here; the nearest is `{near}`. Run `{where}` --help for the flags.
- `err.flag`: `{flag}` is not a flag here. Run `{where}` --help for the flags.
- `err.extra`: `{where}` takes no argument, and got `{word}`. Run `{where}` --help for its usage.
- `err.version`: `{tool}` has no version: `{path}` cannot be read. Run claude plugin install suite@agentik to mend it.
- `err.setup.name`: `{name}` is not a plugin name: a name is lowercase letters, digits and dashes. Run `{setup}` --dry-run for the default set.

- `err.config.tool.near`: `{name}` is not a tool here; the nearest is `{near}`. Run `{config}` for the list.
- `err.config.tool`: `{name}` is not a tool here. Run `{config}` for the list.
- `err.config.key.near`: `{name}` has no setting `{key}`; the nearest is `{near}`. Run `{config}` `{name}` for its keys.
- `err.config.key`: `{name}` has no setting `{key}`. Run `{config}` `{name}` for its keys.
- `err.config.noname`: A tool's name goes before the dot. Run `{config}` for the list.
- `err.config.nokey`: A key goes after the dot. Run `{config}` `{name}` for its keys.
- `err.config.silent`: `{name}`.`{key}` cannot be read: `{name}` gave no settings (`{state}`). Run `{config}` `{name}` for what it gives.
- `err.config.silent.command`: `{name}`.`{key}` cannot be read: `{name}` ships no command. Run `{config}` `{name}` for what it gives.
- `err.config.silent.noread`: `{name}`.`{key}` cannot be read: `{name}` answers, but names no way to read its settings. Run `{config}` `{name}` for what it gives.
- `err.config.read.timed_out`: `{name}`.`{key}` cannot be read: `{name}` answers, but reading its settings ran past 2 s. Run `{config}` `{name}` for what it gives.
- `err.config.read.unreadable`: `{name}`.`{key}` cannot be read: `{name}` answers, but its settings answer cannot be read. Run `{config}` `{name}` for what it gives.
- `err.config.file`: `{fault}`. Mend the file by hand, then run `{config}` `{name}` again.
- `err.status.check`: `{status}` only checks in this version. Run `{status}` --check.
- `err.status.now`: `{value}` is not a time. Give --now in ISO 8601, such as 2026-11-13T12:00:00Z.
- `err.status.ps`: `{path}` cannot be read as a listing. Give --ps a file that ps wrote.
- `err.status.file`: `{fault}`. Mend the file by hand, then run `{status}` --check again.
- `err.config.both`: --changed and --user-files are two answers; ask for one. Run `{config}` --changed first.
- `err.describe.json`: describe prints JSON for other tools, so it needs --json. Run `{config}` suite to read the settings.

## Config

- `config.title`: Tools in the suite: `{count}`, each with its state and its settings.
- `config.count`: `{n}` settings
- `config.count.one`: 1 setting
- `config.differ`: `{n}` changed
- `config.from_table`: from the suite's table
- `config.fault`: `{path}` cannot be read at line `{line}`: `{why}`
- `config.fault.noline`: `{path}` cannot be read: `{why}`
- `config.tool.title`: `{name}`: `{settings}`, `{changed}` changed from the default.
- `config.group`: `{group}`
- `config.changed`: changed
- `config.unknown`: unknown key `{key}`
- `config.badvalue`: `{key}` holds `{value}`, which is not one of its choices
- `config.card.title`: `{name}`.`{key}`
- `config.label.value`: value
- `config.label.summary`: about
- `config.label.default`: default
- `config.label.choices`: choices
- `config.label.set_by`: set by
- `config.label.layer`: layer
- `config.label.command`: run
- `config.label.launch`: at launch
- `config.label.edit`: edit
- `config.label.fixed`: fixed
- `config.label.note`: note
- `config.label.holds`: takes hold
- `config.label.run`: run
- `config.label.file`: user file
- `config.label.needs`: needs
- `config.fixed`: no verb changes it
- `config.live`: now
- `config.later`: at the next start of Claude Code
- `config.table.title`: The suite's table shows where `{name}` keeps its settings.
- `config.table.description`: `{description}`
- `config.table.nocmd`: no command; the user file below holds the settings
- `config.state.timed_out`: `{name}` gives no settings: its describe ran past 2 s, so it was stopped.
- `config.state.unreadable`: `{name}` gives no settings: its describe answer cannot be read.
- `config.state.no_command`: `{name}` is installed but ships no command, so it gives no settings.
- `config.state.noread`: `{name}` answers, but names no way to read its settings.
- `config.state.read_timed_out`: `{name}` answers, but reading its settings ran past 2 s, so it was stopped.
- `config.state.read_unreadable`: `{name}` answers, but its settings answer cannot be read.
- `config.read.timed_out`: reading its settings ran past 2 s
- `config.read.unreadable`: its settings answer cannot be read
- `config.changed.title`: Settings that differ from their defaults: `{count}`.
- `config.changed.none`: Every setting that was read holds its default.
- `config.changed.silent`: These tools gave no settings, so their changes are not here: `{names}`.
- `config.files.silent`: These tools gave no settings, so their user files are not here: `{names}`.
- `config.files.none`: No tool that gave settings names a user file that travels.
- `config.was`: default `{default}`
- `config.set_by`: `{layer}` at `{where}`
- `config.layer`: `{layer}`: `{value}`
- `config.file`: `{path}`
- `hint.config`: next: `{config}` <tool> lists one tool's settings.
- `hint.config.tool`: next: `{config}` `{name}`.<key> shows one setting, where it is set and how to change it.
- `hint.config.card`: next: `{config}` --changed lists every setting that differs from its default.
- `hint.config.back`: next: `{config}` lists every tool and its state.
- `hint.config.changed`: next: `{config}` <tool>.<key> shows where one is set and how to change it.

## The suite's settings

- `describe.summary`: The agentik suite's default set, and the command that manages it.
- `setting.checkouts`: The repos the suite reads across, one path an item.
- `setting.kind`: What this repo is to the suite; hq marks the top of a tree.
- `setting.watcher.match`: The program and the words after it that find the watcher's process.
- `setting.watcher.start`: The line that starts the watcher.
- `setting.watcher.beat`: The file the watcher writes while it runs.
- `setting.watcher.writer`: The name a beat must carry to count as the watcher's own.
- `setting.sources`: Where a tool comes from: a plugin id, or the folder of its plugin.

## Setup

- `setup.title`: Setup plan for `{plugins}`. Nothing is written.
- `setup.title.none`: Setup plan for no plugin, since the manifest lists none. Nothing is written.
- `setup.run`: would run: `{command}`
- `setup.later`: yours to run later: `{command}`
- `setup.add`: add to your shell profile: `{command}`
- `setup.cmd.found`: on PATH at `{path}`
- `setup.cmd.missing`: not on PATH; setup stops here until it is installed
- `setup.cmd.get`: get it: https://claude.com/claude-code
- `setup.python.ok`: Python `{version}` at `{path}`; `{floor}` or newer is needed
- `setup.python.low`: Python `{version}` at `{path}` is older than the `{floor}` minimum; setup stops here
- `setup.market.ok`: known to Claude Code
- `setup.market.missing`: not known to Claude Code; setup would add it
- `setup.plugin.ok`: installed at version `{version}`
- `setup.plugin.missing`: not installed; setup would install it
- `setup.plugin.broken`: listed at version `{version}`, but its folder is gone; setup would install it again
- `setup.launcher.wait`: not placed; step 3 installs the plugin first
- `setup.launcher.missing`: not placed; setup would place it from the plugin
- `setup.launcher.none`: the plugin ships no command, so there is nothing to place
- `setup.launcher.inplace`: the plugin's command runs from the plugin's own folder, so there is nothing to place
- `setup.launcher.ok`: at version `{version}`, the same as the plugin
- `setup.launcher.behind`: at version `{have}`, and the plugin is at `{want}`; setup would place it again
- `setup.launcher.unread`: holds no version line; setup would place it again at `{want}`
- `setup.suite.ok`: at version `{version}`, the same as this command
- `setup.suite.newer`: at version `{have}`, newer than this command's `{want}`; setup leaves it as it is
- `setup.suite.behind`: at version `{have}`, and this command is at `{want}`; setup would place it again
- `setup.suite.unread`: holds no version line; setup would place it again at `{want}`
- `setup.suite.missing`: not placed; setup would place it from this command
- `setup.door.ok`: in place, at this command's version or newer
- `setup.door.above`: not placed, or older than this command's; the line above places it
- `setup.door.place`: not placed, or older than this command's; the install-cli line below places it
- `setup.door.plugin`: not placed, or older than this command's; step 4's install-cli places it
- `setup.door.blocked`: not placed, or older than this command's; setup would place it once step 1 reads ok
- `setup.door.link`: a link, so setup leaves it as it is
- `setup.door.unversioned`: holds no version to compare, so setup leaves it as it is
- `setup.path.ok`: on PATH
- `setup.path.missing`: not on PATH
- `setup.doctor.todo`: setup would check the plugin with its doctor
- `setup.doctor.wait`: step 4 places the launcher first
- `setup.doctor.nocmd`: the plugin ships no command, so it has no doctor to run
- `setup.doctor.none`: no plugin is in the plan, so no doctor runs
- `hint.setup.next`: next: `{command}`
- `hint.setup.blocked`: next: install `{missing}`, then `{setup}` --dry-run again.
- `hint.setup.path`: next: add the line marked add above to your shell profile, then open a new terminal.
- `hint.setup.rest`: next: setup has done what this version can. Step 7's lines check each plugin.
- `hint.setup.done`: next: setup has nothing left to do, since steps 1 to 6 read ok. Step 7's lines check each plugin.
- `setup.ask`: Run these `{count}` commands now? y for yes, n or Enter for no.
- `setup.ask.one`: Run this `{count}` command now? y for yes, n or Enter for no.
- `setup.running`: running `{command}`
- `setup.after`: The plan, read again after the run:
- `setup.ran`: ran: `{command}`, exit `{exit}`
- `setup.ran.wall`: ran: `{command}`, stopped at its `{wall}` s wall
- `setup.ran.start`: ran: `{command}`, which could not start
- `setup.wrote`: wrote: `{path}`
- `setup.nothing`: Setup has nothing to do: no step from 2 to 5 has a line to run.
- `hint.setup.doctor`: next: `{doctor}` checks each plugin.
- `err.setup.yes`: Setup ran nothing, since it cannot ask you here. Run `{setup}` --yes to run the lines above.
- `err.setup.declined`: Setup ran nothing, since the answer was not yes. Run `{setup}` again when you are ready.
- `err.setup.gated`: Setup ran nothing: your gate list names `{path}`, which these steps write. Run `{setup}` from a terminal to approve it.
- `err.setup.blocked`: Setup ran nothing, since step 1 needs `{missing}`. Install it, then run `{setup}` again.
- `err.setup.step`: Setup stopped: `{command}` exited `{exit}` and said `{last}`. Mend that, then run `{setup}` again.
- `err.setup.step.silent`: Setup stopped: `{command}` exited `{exit}` with no output. Mend that, then run `{setup}` again.
- `err.setup.wall`: Setup stopped: `{command}` ran past its `{wall}` s wall and was killed. Its last line: `{last}`. Run `{setup}` again to retry it.
- `err.setup.wall.silent`: Setup stopped: `{command}` ran past its `{wall}` s wall and was killed, with no output. Run `{setup}` again to retry it.
- `err.setup.start`: Setup stopped: `{command}` could not start, since `{last}`. Mend that, then run `{setup}` again.
- `err.setup.todo`: Setup stopped: `{command}` exited 0, but step `{n}` still reads todo. Run `{setup}` --dry-run to see why.
- `err.setup.journal`: Setup could not add its line to the journal at `{path}`, since `{why}`. The report above still holds.
- `setup.ran.stopped`: ran: `{command}`, stopped when setup was interrupted
- `setup.gate.notfile`: it is not a file
- `err.setup.interrupted`: Setup was interrupted, so it stopped `{command}`. Run `{setup}` again to go on.
- `err.setup.interrupted.idle`: Setup was interrupted between steps, with no command running. Run `{setup}` again to go on.
- `err.setup.gate_unread`: Setup ran nothing: your gate list `{path}` cannot be read, since `{why}`. Mend it, or run `{setup}` from a terminal.

## Status

- `status.missing.since`: `{name}`: not running since `{when}`; start it: `{start}`
- `status.missing`: `{name}`: not running; start it: `{start}`
- `status.hung.since`: `{name}`: running but silent since `{when}`; start it: `{start}`
- `status.hung`: `{name}`: running but silent; start it: `{start}`
- `status.unknown`: `{name}`: not checked: ps gave no listing
- `hint.status.unchecked`: `{name}` is not checked, since it needs both match and start in `{path}`. next: add them, then run `{status}` --check.

## Doctor

- `doctor.group.ok`: `{count}` checks
- `doctor.group.one`: 1 check
- `doctor.part.failed`: `{n}` failed
- `doctor.part.warned`: `{n}` to look at
- `doctor.part.ok`: `{n}` ok
- `doctor.part.waiting`: (`{n}` waiting on the rest)
- `doctor.fold`: `{fact}`: `{subjects}`
- `doctor.total`: `{failed}` failed, `{warned}` to look at, `{ok}` ok.
- `doctor.done`: This machine is set up.
- `doctor.fix`: fix: `{command}`
- `doctor.slash`: in Claude Code: `{command}`
- `doctor.door.ok`: `{path}` is at version `{have}`; this command's door is `{want}`
- `doctor.door.behind`: `{path}` is at `{have}`, too old to pass a verb to the suite
- `doctor.door.old`: `{path}` is at version `{have}`, older than `{want}`
- `doctor.door.unread`: `{path}` holds no version to compare: `{have}` there, `{want}` here
- `doctor.door.none`: no agentik command on PATH
- `doctor.shadow.ok`: no command on PATH takes a verb's place
- `doctor.shadow.hit`: `{path}` runs in place of the verb `{word}`; rename or remove it
- `doctor.settings.ok`: `{path}` reads
- `doctor.settings.none`: no user file at `{path}`, so the defaults hold
- `doctor.settings.unchecked`: watcher `{name}` in `{path}` needs both match and start, so status --check skips it
- `doctor.plan.path`: not on PATH
- `doctor.plan.market`: not known to Claude Code
- `doctor.plan.plugin`: not installed
- `doctor.plan.python`: Python `{version}` at `{path}`, older than the `{floor}` minimum
- `doctor.plan.broken`: installed at `{version}`, with its folder gone
- `doctor.plan.behind`: at `{have}`, older than `{want}`
- `doctor.plan.unread`: holds no version line
- `doctor.plan.placed`: not placed
- `doctor.tool.passed`: its doctor passed
- `doctor.tool.failed`: its doctor failed
- `doctor.tool.silent`: its doctor failed, and printed nothing
- `doctor.tool.slow`: its doctor ran past `{secs}` s, so it was stopped
- `doctor.tool.unreadable`: its doctor could not start, or printed more than 1 MiB
- `doctor.tool.nocmd`: no command on PATH, so no doctor
- `hint.doctor.next`: next: `{command}`

## Issue

- `issue.screen.head`: The issue as it would be filed, byte for byte; its first line is the title.
- `issue.screen.text`: `{text}`
- `issue.screen.end`: The issue ends above this line.
- `issue.screen.repo`: It goes to github.com/`{repo}` as a new issue.
- `issue.screen.login`: It is filed as `{login}`, and that login shows on the issue as its author.
- `issue.screen.closed`: A closed issue already holds this failure: `{url}`
- `issue.screen.failed`: The search for an earlier issue failed, so none is known.
- `issue.screen.more`: Press Enter for the next lines of the issue.
- `issue.screen.within`: Press Enter for the rest of this line of the issue.
- `issue.send.ask`: Type send and press Enter to file it; any other answer keeps the draft.
- `issue.send.kept`: Nothing was filed, and the draft is kept as it was.
- `issue.send.web.token`: `{name}` is set and overrides the account gh stores, so the issue goes by the browser.
- `issue.send.web.nogh`: gh is not on PATH, so the issue goes by the browser.
- `issue.send.web.noaccount`: gh holds no github.com account, so the issue goes by the browser.
- `err.issue.send.tty`: send needs a terminal to type in, and this process has none. Run it from your own terminal.
- `err.issue.send.inside`: send files nothing from inside Claude Code. Run it from your own terminal.
- `err.issue.send.parent`: send files nothing from a process that Claude Code started. Run it from your own terminal.
- `err.issue.send.ps`: send cannot read the process list, so it cannot tell what started it. Run it from your own terminal.
- `err.issue.send.as`: gh holds `{count}` github.com accounts, so send needs the login to file as. Run gh auth switch --user LOGIN, then name that login.
- `err.issue.send.inactive`: `{login}` is not the active github.com account in gh. Run gh auth switch --user `{login}`, then send again.
- `err.issue.send.line`: Line `{line}` of the draft fails the `{kind}` check, so nothing was sent. Mend that line, then send again.
- `err.issue.send.changed`: The approved issue changed after it was shown, so nothing was sent. Run send again to see it.
- `err.issue.send.unapproved`: This issue holds no approval that is still good, since each is used once, so nothing was sent. Run send again to see it.
- `err.issue.send.token`: `{name}` is set and overrides the account gh stores, so nothing was sent through gh. Unset it and send again, or file the issue by the browser.
- `err.issue.send.switched`: The active github.com account in gh is not `{login}`, the login the screen showed, so nothing was sent. Run gh auth switch --user `{login}`, then send again.
- `err.issue.send.failed`: gh exited `{code}` and filed nothing: `{last}`. The draft is kept; run send again.
- `err.issue.send.timeout`: gh ran past `{secs}` s and was stopped, so whether the issue was filed is unknown. Search the repo before you send again.
- `err.issue.send.flood`: More input came on the terminal right after the word, so nothing was sent. Run send again and type the word once.
- `err.issue.send.early`: Input came on the terminal before the question could be read, so nothing was sent. Run send again and answer once the question shows.
- `err.issue.send.small`: The terminal is too small to show a line of the issue beside its question, so nothing was sent. Make the window larger, then send again.
- `err.issue.send.nogh`: gh could not start, so nothing was filed. Install gh, or file the issue by the browser.
