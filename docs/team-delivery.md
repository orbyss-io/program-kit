# Team delivery development

Program Kit includes a disabled-by-default `program-kit-delivery` extension with offline
preparation, profiles, four work-item templates and the common core authority boundary.
The Phase 2 implementation adds reviewed Azure setup, discovery, planning and repository activation
for refinement. Its real human portal acceptance case passed. GitHub activation,
full synchronization and execution claims belong to later phases.
Installing or upgrading the kit performs no delivery-provider calls or writes.

Use `speckit.program-kit-delivery.configure` to prepare a shared policy and repository binding,
and `speckit.program-kit-delivery.refine` for guided Epic → Feature → Requirement → optional Task
content. Both human platform entries and agent-created drafts use the same validators. Minimal
epics need a title, outcome and business owner. Refinement readiness, implementation admission,
verified delivery and business acceptance remain distinct.

The installed [delivery reference](../extensions/program-kit-delivery/references/delivery.md)
documents the product schema, preparation records and exact limitations. The [Phase 1 decisions](backlog-delivery-phase-1-decisions.md)
record the accepted design; [Phase 0 evidence](delivery/phase-0-evidence.md) remains historical.

The checked-in binding/history and pinned profile snapshot are consumer-owned. Upgrades preserve
their bytes; machine-local configuration cannot override them. Default-disabled older consumers
continue to work without the delivery extension. An enabled consumer with missing runtime or
provider admission fails explicitly at governed checkpoints, including direct implementation
preflight. A missing connected configuration does not silently restore local authority.

Use `speckit.program-kit-delivery.azure` for the reviewed Azure journey described in the
[Azure reference](../extensions/program-kit-delivery/references/azure-planning.md). Untagged portal
epics are discoverable within the selected project and areas; discovery does not approve them.
Activation verifies native capabilities, identities, the pinned profile and coordinator permissions.
Only refinement admission is implemented. Profile changes and disconnection still require later
reviewed operations; hand-written history cannot restore local authority. See the
[Phase 2 decisions](backlog-delivery-phase-2-decisions.md) and [acceptance evidence](delivery/phase-2-evidence.md).
This development branch is not a release announcement.
