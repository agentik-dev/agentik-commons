# Messages

Each item below is one message the command prints, by its id; the writer in `term.py` prints it.

## Help

- `help.title`: `{tool}` `{version}` manages the agentik suite's default set of plugins.
- `help.usage`: usage: `{tool}` <verb> [<name>...] [flags]
- `help.verbs`: verbs
- `help.flags`: flags
- `help.path`: agentik commands on PATH
- `help.path.none`: No agentik command is on PATH yet.
- `hint.help`: next: `{tool}` setup --dry-run shows what setup would do on this machine.
- `hint.verb`: next: `{tool}` help lists every verb and the agentik commands on PATH.
- `verb.help`: List the verbs, the flags and the agentik commands on PATH.
- `verb.version`: Print the suite's version.
- `verb.setup`: Plan the suite's setup. This version only plans, so pass --dry-run.
- `verb.config`: Show each tool's settings, then one tool's, then one setting and how to change it.
- `verb.describe`: Print the suite's own answer, in JSON, for other tools to read.
- `usage.help`: usage: `{tool}` help [<verb>] [flags]
- `usage.version`: usage: `{tool}` version [flags]
- `usage.setup`: usage: `{tool}` setup --dry-run [<plugin>...] [flags]
- `usage.config`: usage: `{tool}` config [<tool>[.<key>]] [flags]
- `usage.describe`: usage: `{tool}` describe [config [<key>]] --json
- `flag.json`: Print one JSON object on stdout, and nothing else there.
- `flag.quiet`: Print no hints and no progress.
- `flag.no_color`: Print no colour, on a terminal too.
- `flag.help`: Show the usage and the flags.
- `flag.dry_run`: Show the plan, and write nothing.
- `flag.yes`: Answer yes to every question; this version asks none.
- `flag.changed`: List every setting that differs from its default.
- `flag.user_files`: Print the path of each user file that travels, one a line.

## Version

- `version.line`: `{tool}` `{version}`

## Errors

- `err.verb.near`: `{word}` is not a verb; the nearest is `{near}`. Run `{tool}` --help for the list.
- `err.verb`: `{word}` is not a verb. Run `{tool}` --help for the list.
- `err.flag.near`: `{flag}` is not a flag here; the nearest is `{near}`. Run `{where}` --help for the flags.
- `err.flag`: `{flag}` is not a flag here. Run `{where}` --help for the flags.
- `err.extra`: `{where}` takes no argument, and got `{word}`. Run `{where}` --help for its usage.
- `err.setup.plan_only`: Setup needs --dry-run: version `{version}` only plans, and it wrote nothing. Run `{tool}` setup --dry-run for the plan.
- `err.version`: `{tool}` has no version: `{path}` cannot be read. Run claude plugin install suite@agentik to mend it.
- `err.setup.name`: `{name}` is not a plugin name: a name is lowercase letters, digits and dashes. Run `{tool}` setup --dry-run for the default set.

- `err.config.tool.near`: `{name}` is not a tool here; the nearest is `{near}`. Run `{tool}` config for the list.
- `err.config.tool`: `{name}` is not a tool here. Run `{tool}` config for the list.
- `err.config.key.near`: `{name}` has no setting `{key}`; the nearest is `{near}`. Run `{tool}` config `{name}` for its keys.
- `err.config.key`: `{name}` has no setting `{key}`. Run `{tool}` config `{name}` for its keys.
- `err.config.noname`: A tool's name goes before the dot. Run `{tool}` config for the list.
- `err.config.nokey`: A key goes after the dot. Run `{tool}` config `{name}` for its keys.
- `err.config.silent`: `{name}`.`{key}` cannot be read: `{name}` is `{state}`. Run `{tool}` config `{name}` for what it gives.
- `err.config.silent.command`: `{name}`.`{key}` cannot be read: `{name}` ships no command. Run `{tool}` config `{name}` for what it gives.
- `err.config.silent.noread`: `{name}`.`{key}` cannot be read: `{name}` answers, but names no settings read. Run `{tool}` config `{name}` for what it gives.
- `err.config.read.timed_out`: `{name}`.`{key}` cannot be read: `{name}` answers, but its settings read ran past 2 s. Run `{tool}` config `{name}` for what it gives.
- `err.config.read.unreadable`: `{name}`.`{key}` cannot be read: `{name}` answers, but its settings read cannot be read. Run `{tool}` config `{name}` for what it gives.
- `err.config.file`: `{fault}`. Mend the file by hand, then run `{tool}` config `{name}` again.
- `err.config.both`: --changed and --user-files are two answers; ask for one. Run `{tool}` config --changed first.
- `err.describe.json`: describe prints JSON for other tools, so it needs --json. Run `{tool}` config suite to read the settings.

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
- `config.state.noread`: `{name}` answers, but names no settings read.
- `config.state.read_timed_out`: `{name}` answers, but its settings read ran past 2 s, so it was stopped.
- `config.state.read_unreadable`: `{name}` answers, but its settings read cannot be read.
- `config.read.timed_out`: its settings read ran past 2 s
- `config.read.unreadable`: its settings read cannot be read
- `config.changed.title`: Settings that differ from their defaults: `{count}`.
- `config.changed.none`: Every setting read holds its default.
- `config.changed.silent`: These tools did not answer, so their settings are not here: `{names}`.
- `config.files.silent`: These tools did not answer, so their user files are not here: `{names}`.
- `config.files.none`: No tool that answered names a user file that travels.
- `config.was`: default `{default}`
- `config.set_by`: `{layer}` at `{where}`
- `config.layer`: `{layer}`: `{value}`
- `config.file`: `{path}`
- `hint.config`: next: `{tool}` config <tool> lists one tool's settings.
- `hint.config.tool`: next: `{tool}` config `{name}`.<key> shows one setting, where it is set and how to change it.
- `hint.config.card`: next: `{tool}` config --changed lists every setting that differs from its default.
- `hint.config.back`: next: `{tool}` config lists every tool and its state.
- `hint.config.changed`: next: `{tool}` config <tool>.<key> shows where one is set and how to change it.

## The suite's settings

- `describe.summary`: The agentik suite's default set, and the command that manages it.
- `setting.checkouts`: The repos the suite reads across, one path an item.
- `setting.kind`: What this repo is to the suite; hq marks the top of a tree.
- `setting.watcher.match`: What the watcher looks for.
- `setting.watcher.start`: The command the watcher starts.
- `setting.watcher.beat`: How often the watcher looks.
- `setting.watcher.writer`: Who writes what the watcher reads.

## Setup

- `setup.title`: Setup plan for `{plugins}`. Nothing is written.
- `setup.title.none`: Setup plan for no plugin, since the manifest lists none. Nothing is written.
- `setup.run`: run: `{command}`
- `setup.add`: add to your shell profile: `{command}`
- `setup.cmd.found`: on PATH at `{path}`
- `setup.cmd.missing`: not on PATH; setup stops here until it is installed
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
- `setup.launcher.ok`: at version `{version}`, the same as the plugin
- `setup.launcher.behind`: at version `{have}`, and the plugin is at `{want}`; setup would place it again
- `setup.launcher.unread`: holds no version line; setup would place it again at `{want}`
- `setup.suite.ok`: at version `{version}`, the same as this command
- `setup.suite.behind`: at version `{have}`, and this command is at `{want}`; this version cannot place it, so run `{path}`
- `setup.suite.unread`: holds no version line; this version cannot place it, so run `{path}`
- `setup.suite.missing`: not placed; a later version places it. Until then, run `{path}`
- `setup.door.ok`: in place
- `setup.door.missing`: not placed; the first install-cli run in step 4 places it
- `setup.door.place`: not placed; the install-cli line below places it
- `setup.door.blocked`: not placed; setup would place it once step 1 reads ok
- `setup.path.ok`: on PATH
- `setup.path.missing`: not on PATH
- `setup.doctor.todo`: setup would check the plugin with its doctor
- `setup.doctor.wait`: step 4 places the launcher first
- `setup.doctor.nocmd`: the plugin ships no command, so it has no doctor to run
- `setup.doctor.none`: no plugin is in the plan, so no doctor runs
- `hint.setup.todo`: next: run each `run:` line above, in order, then `{tool}` setup --dry-run again.
- `hint.setup.blocked`: next: install `{missing}`, then `{tool}` setup --dry-run again.
- `hint.setup.path`: next: add the line marked add above to your shell profile, then open a new terminal.
- `hint.setup.rest`: next: setup has done what this version can. Step 7's lines check each plugin.
- `hint.setup.done`: next: setup has nothing left to do, since steps 1 to 6 read ok. Step 7's lines check each plugin.
