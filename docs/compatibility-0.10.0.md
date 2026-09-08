# Program Kit 0.10.0 compatibility report

0.10.0 is a pre-1.0 product-boundary and governance release. Program Kit's AI extensions,
governance, generators, preset, and workflow advance to `0.10.0`. Reusable runtime source and
publication move to the independently versioned Orbyss Foundation, Orbyss Forms, and Orbyss
Localization repositories. Program Kit pins Foundation `0.1.0`, Forms `0.1.1`, and Localization
`0.1.1`; it no longer builds or publishes NuGet, npm, or host-image artifacts.

Existing consumers do not receive an automatic package-ID migration. They must replace
`ProgramKit.*` dependencies with the documented `Orbyss.Foundation.*`, `Orbyss.Forms.*`, and
`Orbyss.Localization.*` packages. Program Kit never removes or hides legacy package versions. Its
read-only compatibility gate verifies the recorded legacy inventory and all 50 replacement NuGet
packages at their independently pinned family versions.

Bootstrap intake and architecture-map schemas advance together to `1.1`. This deliberately replaces
the exploratory skinny 1.0 shape; there is no dual validator or migration path. This release targets
consumers performing their first intake, and they generate 1.1 from the start.

The 1.1 model requires classified subdomains, enriched bounded contexts, owned modules/contracts,
typed cross-context relationships, multidimensional Program Kit capability bindings, complete
journey traceability, dynamic journey views, candidate slices, and provisional founding decision
candidates. System Context remains C4; strategic DDD views use Structurizr custom elements so
bounded contexts and modules are not misrepresented as peer software systems.

Draft visual review remains read-only and confirmation-neutral. Architecture turns founding
candidates into real Proposed ADRs. The final bootstrap architecture gate accepts only the exact
hash-bound founding ADR bundle and refreshes its canonical map/projection bindings.
