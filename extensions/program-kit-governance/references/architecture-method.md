# Architecture method

## Artifact hierarchy

<!-- program-kit:knowledge-rule context.architecture-artifact-hierarchy -->
1. Project constitution: highest ratified governance authority and amendment policy.
2. Confirmed product intent/intake: user intent, classified gaps, and starting assumptions interpreted under the constitution.
3. Canonical architecture map and architecture baseline: the current coherent model, views, constraints, quality scenarios, risks, and ADR links.
4. ADRs: history and authority for significant project-specific choices.
5. Specification roadmap: epic outcomes, priorities, dependencies and linked candidate features.
6. Feature specifications: implementable vertical behavior slices constrained by the earlier authority.
7. Plans and tasks: delivery design and work decomposition.
8. Implementation and verification evidence.

The confirmed intake may contain founding decision candidates. They are evidence-backed prepwork,
not authority. Architecture verifies them against the constitution, narrows research to material
uncertainties, and records consequential candidates as Proposed ADRs with their alternatives and
consequences intact. Record the human's explicit acceptance of the named architecture choices as
individual ADR decisions. Constitution ratification remains a separate decision; unrelated proposals
retain their actual status. No founding-bundle hash or approval receipt establishes acceptance.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:decision-rule authority-conflicts -->
<!-- program-kit:knowledge-rule principle.authority-conflicts -->
Compare accepted decisions with the constitution and applicable adopted engineering constraints.
Acceptance is not an implicit waiver: surface conflicts before dependent design or implementation.
Preserve history and resolve substantive architecture changes through explicit scoped ADR review;
an exception must identify its governing authority, consequences and current verification.
<!-- /program-kit:knowledge-rule -->
<!-- /program-kit:decision-rule -->

<!-- program-kit:knowledge-rule context.constitution-roadmap-authority -->
The constitution is not an ordinary feature specification and never enters the feature
specification/plan/task/implement lifecycle. The last ratified constitution remains the governing baseline
while amendments are proposed. Follow its amendment policy for substantive changes, obtain explicit human
ratification and record the actual decision's date/context and status in the constitution. Drafting an
amendment does not make it authoritative or automatically revoke the existing ratification. A toolkit
refresh or representation-only edit does not require amending or re-ratifying the constitution.
No hash-bound validation, toolkit receipt or extra ceremony is required to record human authority.

The specification roadmap owns intended epic outcomes, completion conditions, priorities and linked
feature seeds. An epic can have several independently scoped feature specifications; a domain can
support several epics. The roadmap recommends a start while specification intake settles the exact
feature commission. Distinguish intended work from exploratory options. Readiness concerns the
actual affected work and due decisions; epic membership alone creates no dependency on every sibling.
Legacy specification-oriented entries remain readable with their original meaning.
<!-- /program-kit:knowledge-rule -->

## Design tasks before feature slices

<!-- program-kit:knowledge-rule principle.focused-architecture-design -->
Architecture gaps are resolved as focused design tasks. Each task frames one decision, gathers evidence, compares credible alternatives, records consequences, updates views, and identifies which specifications it enables. Examples include isolation boundaries, queue/outbox semantics, tenancy and authorization, contract versioning, package security, reproducibility, signing/provenance, and recovery.

Design tasks do not pass through `speckit.implement` as application work. They update evidence,
Proposed ADRs, architecture views, traceability, and the roadmap entries they unblock.
<!-- /program-kit:knowledge-rule -->

## Outcome-oriented decomposition

<!-- program-kit:knowledge-rule principle.outcome-decomposition -->
Use `vertical-slicing.md` as the default delivery method and `modularity-and-contracts.md` for
ownership and dependency boundaries. Candidate slices begin with an actor, trigger, or intent and
end in an observable, verified outcome. Technical layers may exist inside a module, but they are not
the primary specification or delivery units.

The architecture baseline records bounded contexts, modules, features, slices, contract owners, data
owners, and allowed dependency edges. A slice may cross internal technical concerns without crossing
those ownership boundaries invisibly.
<!-- /program-kit:knowledge-rule -->

## Status discipline

<!-- program-kit:knowledge-rule context.accepted-design-status -->
Use `default-adoption.md` to explain applicable technical defaults and preserve explicit choices.
Record consequential proposed decisions and their actual human acceptance in normal ADRs; keep
Rejected, Deprecated and Superseded decisions linked to their history. Routine defaults need no
separate assessment packet. Human agreement remains real; no hash-bound bootstrap gate or toolkit
receipt is required to remember it, and a representation change alone does not reopen its meaning.
<!-- /program-kit:knowledge-rule -->

## Living architecture

<!-- program-kit:knowledge-rule principle.living-architecture -->
Architecture changes in the same change set as the decision or implementation that invalidates it. CI checks machine-verifiable structure and traceability; human review owns architectural judgment.
<!-- /program-kit:knowledge-rule -->
