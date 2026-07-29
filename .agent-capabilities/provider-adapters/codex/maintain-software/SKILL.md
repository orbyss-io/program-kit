---
name: maintain-software
description: Implement one explicit bounded architecture-compatible consumer software change. Use directly for a clearly scoped compatible change, not for design, exact approved-plan execution, read-only work, or Program Kit contributor maintenance.
---

# maintain-software

Verify setup and load the complete canonical Program Kit capability by invoking:

`program-kit capabilities preflight maintain-software --workspace-root .`

`program-kit capabilities read maintain-software --workspace-root .`

Read and follow the complete returned definition before acting. If either
command is unavailable or reports stale setup, stop and report a Program Kit
setup blocker.

This provider skill is only trigger/registration metadata. The installed
Program Kit CLI owns delivery of the canonical provider-neutral capability.
