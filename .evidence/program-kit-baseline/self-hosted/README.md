# Program Kit self-hosted baseline

This directory is the `PK-W080` self-hosted review set.

`architecture-design.json` and `implementation-plan.json` are the canonical
Program Kit contract instances. The plan is marked `superseded` because it is a
non-authoritative self-hosted representation: the exact approved bootstrap plan
and approval record remain the implementation authority. No new approval is
minted here.

`architecture-design.md`, `implementation-plan.md`, and the three `.dot` files
are deterministic, disposable projections. `bootstrap-comparison.json` records
the explicit mapping and differences between the historical bootstrap inputs
and the self-hosted instances. `approval-relationship.json` reports lineage to
the existing approval without changing it.

`request-evidence.md` records the actual post-registration human continuation
that started this work. `development-receipt.json` binds that event to the exact
registered `implement-software-plan` capability bytes and does not claim that
the capability authored any pre-existing bootstrap source.

The bootstrap source files remain under `program-kit/bootstrap/` and are not
copied, normalized, or rewritten by this review set.
