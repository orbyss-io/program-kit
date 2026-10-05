# Program Kit 0.12.8

This patch fixes task-generation instruction conflicts and adds incremental drafting.
Active component, persistence, .NET and API references now use the ordinary plan/tasks
and engineering checks. They no longer require additional adoption, ownership or API-proof
dossiers or new approval dependencies before drafting tasks.

Phase-context returns applicable summaries with exact section pointers for optional focused
lookup. It filters by phase, excludes generated tasks and historical dossiers from applicability
detection, and supports a single-obligation follow-up. It does not ask the agent to reread entire
references. For the reported wall-cut-list feature, the corrected projection retains all 17
applicable obligations in about 12.6 KB. The fast Python commands and long interrupted agent
turns did not reproduce a Python deadlock; the effect on agent latency remains unverified.

The installed before_tasks hook and composed task template instruct the agent to save tasks.md
after required inputs, then save every completed phase. A small helper stores drafting progress
inside tasks.md with atomic checkpoint replacement. Resume preserves phases, task IDs, checked
boxes and consumer edits, reports changed inputs for scoped review, and rejects incomplete or
duplicate-ID drafts before finalization. Unmarked existing task documents remain intact and
can be completed directly. Mandatory read-only analyze runs after task drafting is complete.

Generating tasks schedules unresolved compatibility/admission inputs and decisions as owned
prerequisites with explicit dependencies. It does not execute probes, provision services,
restart bootstrap, change approvals or claim runtime evidence. Constitutional test-first work,
security, ownership, exact dependency decisions, contract checks and real-provider verification
remain required before dependent implementation or completion.

## Upgrade from 0.12.7

Use the verified release-owned updater's --plan mode, inspect the migration, then install the
patch through the maintained updater. Installation updates managed toolkit instructions and
adds the task-draft helper; it does not generate or replace consumer tasks automatically.
Verify installation coherence and retained dependency inputs. Resume the feature's normal
tasks command after installation. No bootstrap restart, approval renewal, constitution amendment,
native-lock rewrite, data migration or dependency-profile transition is required by this patch.

Foundation, Forms, Localization, host images, SDKs and qualified dependency profiles retain
their existing independent versions and evidence. Existing consumer profiles keep their exact pins.
Consumers requiring a new substantive design or dependency choice still use their normal review.

## Validation and recovery

Regressions cover active reference consistency, bounded context, phase filtering, draft resume,
changed-input review, interrupted writes, consumer-edit preservation and installed tasks/analyze
hooks. Publication requires the complete deterministic local Release gate and complete tagged CI,
including Firefox and public installation/upgrade smoke checks. These checks do not start agents
or establish consumer acceptance.

On interruption, preserve tasks.md and run the normal tasks command again; review only changed
inputs and affected phases. Preserve failed updater/validation evidence and retry the same verified
release. Never fabricate a completed checkpoint, approval or compatibility result. Unsupported
layouts and conflicting consumer edits remain protected by the updater.
