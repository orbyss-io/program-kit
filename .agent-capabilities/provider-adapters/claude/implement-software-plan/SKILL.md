---
name: implement-software-plan
description: Execute an exact human-approved repository software plan under its recorded approval. Use directly only when the exact approved artifacts and authorized work unit are supplied.
---

# implement-software-plan

Verify setup and load the complete canonical Program Kit capability by invoking:

`program-kit capabilities preflight implement-software-plan --workspace-root .`

`program-kit capabilities read implement-software-plan --workspace-root .`

Read and follow the complete returned definition before acting. If either
command is unavailable or reports stale setup, stop and report a Program Kit
setup blocker.

This provider skill is only trigger/registration metadata. The installed
Program Kit CLI owns delivery of the canonical provider-neutral capability.
