# Tool and integration selection

Select capabilities before products. Research current options at bootstrap time because ecosystems, compatibility, maintenance, and security change.

For each candidate record:

- capability and risk addressed;
- fit with detected technologies and architecture;
- active maintenance, release recency, license, adoption, and exit cost;
- Spec Kit compatibility and integration mechanism;
- permissions, scripts, network behavior, and supply-chain trust;
- enforcement strength and false-positive/false-negative profile;
- lifecycle trigger, version pin, upgrade test, and removal path;
- alternatives and reasons for selection or rejection.

Community Spec Kit catalogs are discovery inputs, not endorsements. Inspect extension commands, hooks, scripts, and transitive tools. Mandatory quality controls belong in deterministic CI even when Spec Kit hooks give earlier feedback.

Evaluate rather than automatically install:

- Architecture Governance for ADR/architecture artifact gates.
- ADR tooling or a local adapter when the current ADR kit adapter is incompatible.
- API Evolve when an externally versioned contract appears.
- Reqnroll BDD for valuable multistep executable examples in .NET contexts.
- ArchUnitNET for compiled .NET dependency and layering rules.
- Structurizr DSL/C4 and arc42 when architecture-as-code and navigable documentation fit.

