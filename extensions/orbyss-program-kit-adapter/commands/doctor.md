---
description: Validate exact Program Kit adapter readiness without selecting, activating, authorizing, or constructing.
---

# Program Kit adapter doctor

Determine whether the requested scope is `base` or one explicitly named
feature. Do not infer applicability, a profile, or authority from prose.

Invoke the installed adapter executable with an exact argument vector:

```text
dotnet <extension-root>/tools/program-kit-spec-kit-adapter.dll doctor --workspace <workspace> --request <request> --format json
```

Treat only the schema-valid adapter result as authoritative. Base doctor may
succeed with zero selected profiles. Report installed, available, selected,
activated, and authorized separately. Never invoke Program Kit initialization,
authority recording, construction, a shell command, network access, telemetry,
or source upload from this instruction.
