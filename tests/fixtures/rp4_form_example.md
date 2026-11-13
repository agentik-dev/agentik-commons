lantern doctor: failing: resolved, meter

**Ran:** `agentik lantern doctor`, exit 2
**Happened:** `doctor: failing: resolved, meter`
**Expected:** `doctor passes in a fresh clone of billing-api, before any lantern`
**Versions:** lantern 2.0.0-alpha.101 (1f3a9c0d2b7e), suite 0.6.0, door 0.2.0, Claude Code 2.1.323, Darwin 27.0.0 arm64, Python 3.9.6, at a terminal

<details><summary>Diagnosis: 1 failed, 0 warned, 21 passed</summary>

| tool | status | check | detail |
|---|---|---|---|
| lantern | fail | `doctor` | `doctor: failing: resolved, meter` |

Plugins: lantern 2.0.0-alpha.101, harmonics 0.21.17, ledger 1.6.3, suite 0.6.0, and 1 other

Last lines:
```
no profile resolved for <path-1>
doctor: failing: resolved, meter
```

</details>

agentik-issue/1 lantern 2.0.0-alpha.101 2bcc624a2914
