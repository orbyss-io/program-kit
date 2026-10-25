---
description: Refresh owned preview toolkit files while preserving authored work and local choices.
---

Read `references/consumer-upgrade.md`. Select the exact inspected target release and its tooling
archive, outside the consumer. For preview-to-preview replacement, retain the previous preview's
exact tooling source so native ownership/customization checks can authenticate the old installation.

From the consumer root, inspect the supported replacement plan:

```sh
python <new-tooling>/scripts/upgrade_program_kit.py --release-root <new-tooling> --previous-release-root <old-preview-tooling> --target . --plan
```

Apply by removing `--plan` only after reviewing the concrete result. Run installation/update yourself
from the normal user-owned terminal. A device mismatch needs the matching human preparation script;
the agent must not install device SDKs/runtimes or substitute another interpreter.

The 0.x to 1.0.0-preview.1 boundary uses a clean checkout and explicit re-onboarding. Preserve source,
architecture documents, locks, task progress and old evidence as inputs; do not convert old workflow
history into approval or silently delete customizations. The updater refuses unsupported 0.x state
before mutation. Later previews preserve authored product/specification work; announced incompatible
changes require explicit review.

A toolkit refresh does not choose new dependency versions, alter consumer design or authorize
provider/data operations, publication or an external rollout. Review substantive changes with their
normal owners, continue ordinary native Spec Kit phases, and run the actual affected project checks.
