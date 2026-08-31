---
description: Revoke stale ratification evidence before drafting or amending the constitution.
scripts:
  py: scripts/governance_state.py begin
---

## Purpose

The project constitution is the highest project governance artifact. It is not a feature
specification and must be drafted without invoking `speckit.specify`.

## Work

Before changing governance state, verify that the initialized project's active integration exposes
the literal core command `speckit.constitution` from the installed Spec Kit version. For Codex this
means `.agents/skills/speckit-constitution/SKILL.md`; for another integration use that integration's
generated core-command location. Do not substitute a Program Kit command or locally reconstructed
prompt. If the core command is absent, stop and report that Spec Kit initialization or installation
must be repaired.

From the project root, run the installed Program Kit governance-state script with an available
Python 3 interpreter:

```text
{SCRIPT}
```

This must complete before `speckit.constitution` drafts or amends the constitution. It changes only
`.specify/memory/constitution-ratification.json` to `Draft` and preserves any prior ratification as
audit context. Do not edit the constitution, architecture, application code, or specification files.

If the script or interpreter is unavailable, stop with the exact error. Never leave a stale
`Ratified` marker in place while constitution drafting proceeds.
