# Team delivery development

Program Kit includes a disabled-by-default `program-kit-delivery` extension. Phase 1 supplies
offline preparation, profiles, four work-item templates and the common core authority boundary.
Azure/GitHub consumer activation, synchronization and execution claims are not available yet.
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

Phase 1 has no activation, profile-change or disconnect receipt writer. It also cannot verify a
disconnect claim and therefore cannot use hand-written history to restore local authority. Local
drafting, profile checks and technical-only validation remain useful while provider admission is
unavailable. This development branch is not a release announcement.
