{tool-0} doctor: failing: resolved, meter

**Ran:** `agentik {tool-0} doctor`, exit 2
**Happened:** `doctor: failing: resolved, meter`
**Expected:** `doctor passes in a fresh clone of billing-api, before any {tool-4}`
**Versions:** suite 0.6.0, {tool-0} 2.0.0-alpha.101, Claude Code unreadable, {system}, at a terminal

<details><summary>Diagnosis: 1 failed, 10 warned, 6 passed</summary>

| tool | status | check | detail |
|---|---|---|---|
| {tool-0} | fail | `doctor` | `doctor: failing: resolved, meter` |
| suite | warn | `door` | `no agentik command on PATH` |
| suite | warn | `plugin {tool-4}@agentik` | `not installed` |
| suite | warn | `plugin {tool-1}@agentik` | `not installed` |
| suite | warn | `plugin {tool-0}@agentik` | `installed at 2.0.0-alpha.101, with its folder gone` |
| suite | warn | `launcher ~/.local/bin/agentik-{tool-4}` | `not placed` |
| suite | warn | `launcher ~/.local/bin/agentik-{tool-1}` | `not placed` |
| suite | warn | `launcher ~/.local/bin/agentik-{tool-0}` | `not placed` |
| suite | warn | `suite ~/.local/bin/agentik-suite` | `not placed` |
| suite | warn | `door ~/.local/bin/agentik` | `not placed` |
| suite | warn | `path ~/.local/bin` | `not on PATH` |

Plugins: {tool-0} 2.0.0-alpha.101, suite 0.6.0, and 0 other

Last lines:
```
no profile resolved for <path-1>
doctor: failing: resolved, meter
```

</details>

agentik-issue/1 {tool-0} 2.0.0-alpha.101 dda8af236ed7
