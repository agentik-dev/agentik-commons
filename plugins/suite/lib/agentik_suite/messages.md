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
- `usage.help`: usage: `{tool}` help [<verb>] [flags]
- `usage.version`: usage: `{tool}` version [flags]
- `usage.setup`: usage: `{tool}` setup --dry-run [<plugin>...] [flags]
- `flag.json`: Print one JSON object on stdout, and nothing else there.
- `flag.quiet`: Print no hints and no progress.
- `flag.no_color`: Print no colour, on a terminal too.
- `flag.help`: Show the usage and the flags.
- `flag.dry_run`: Show the plan, and write nothing.
- `flag.yes`: Answer yes to every question; this version asks none.

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
- `setup.plugin.broken`: listed at version `{version}`, but its files are not whole; setup would install it again
- `setup.launcher.wait`: not placed; step 3 installs the plugin first
- `setup.launcher.missing`: not placed; setup would place it from the plugin
- `setup.launcher.ok`: at version `{version}`, the same as the plugin
- `setup.launcher.behind`: at version `{have}`, and the plugin is at `{want}`; setup would place it again
- `setup.launcher.unread`: holds no version line; setup would place it again at `{want}`
- `setup.suite.ok`: at version `{version}`, the same as this command
- `setup.suite.behind`: at version `{have}`, and this command is at `{want}`; this version cannot place it, so run `{path}`
- `setup.suite.unread`: holds no version line; this version cannot place it, so run `{path}`
- `setup.suite.missing`: not placed, and this version cannot place it; run `{path}` instead
- `setup.door.ok`: in place
- `setup.door.missing`: not placed; the first install-cli run in step 4 places it
- `setup.door.place`: not placed; the install-cli line below places it
- `setup.path.ok`: on PATH
- `setup.path.missing`: not on PATH
- `setup.doctor.todo`: setup would check the plugin with its doctor
- `setup.doctor.wait`: step 4 places the launcher first
- `setup.doctor.none`: no plugin is in the plan, so no doctor runs
- `hint.setup.todo`: next: run each `run:` line above, in order, then `{tool}` setup --dry-run again.
- `hint.setup.blocked`: next: install `{missing}`, then `{tool}` setup --dry-run again.
- `hint.setup.rest`: next: steps 1 to 6 hold no line to run. Each row not marked ok says what is left.
- `hint.setup.done`: next: setup has nothing left to do, since steps 1 to 6 read ok. Step 7's lines check each plugin.
