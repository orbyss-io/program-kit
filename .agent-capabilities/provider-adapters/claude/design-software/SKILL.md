---
name: design-software
description: Design, plan, revise, or converge repository software from current source truth, producing a review set and stopping for explicit human approval.
---

# design-software

Verify setup and load the complete canonical Program Kit capability by invoking:

`program-kit capabilities preflight design-software --workspace-root .`

`program-kit capabilities read design-software --workspace-root .`

Read and follow the complete returned definition before acting. If either
command is unavailable or reports stale setup, stop and report a Program Kit
setup blocker.

This provider skill is only trigger/registration metadata. The installed
Program Kit CLI owns delivery of the canonical provider-neutral capability.
