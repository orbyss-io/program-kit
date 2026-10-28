---
description: Inspect or apply explicit engineering setup changes.
scripts:
  py: scripts/repository_sync.py
---

Use setup synchronization when choosing Program Kit's engineering generators to add or change
actual project, package or composition inputs. It is not a prerequisite for native Spec Kit phases.
Run `{SCRIPT} plan --phase implementation --feature-dir <feature>` for an inspectable preview,
then `{SCRIPT} apply --phase implementation --feature-dir <feature>` to apply mechanical metadata.
An optional `--plan-digest` protects a reviewed change against intervening generator-input changes.
Human architecture and product reviews remain the decisions recorded in the project documents.

Use the selected native restore/build/test commands for normal engineering. Source/package conflicts,
provider transitions, registry permissions and trust failures need their actual diagnostic resolved.
A missing review receipt or changed document formatting does not establish an application problem.
Do not write per-feature success attestations or duplicate package declarations.

Preview toolkit updates use `upgrade_program_kit.py` with the prior release inputs. That operation
refreshes native toolkit components and preserves authored product/specification work; it does not
advance application dependency versions or establish application compatibility. The 0.x boundary
requires fresh intake using existing architecture documents as inputs.

For a selected Foundation composition, synchronization can materialize configuration and
feature-owned registration/provider seams through the same preview/apply ownership flow.
Link the useful configuration documents and redacted settings. Materialization alone establishes
neither runtime readiness nor product acceptance. Start a runtime or provision a service only when
the selected action or test needs it. The generic implementation hook starts no application.
Inspect actual activation outcomes and use the relevant native diagnostic or helper repair route.

Missing or incompatible device tools need a platform-appropriate preparation script for the human.
Agents may restore declared project packages using existing tools. Preserve captured package pins,
locks and consumer-owned configuration across toolkit updates.
