# Default adoption

## Bootstrap promise

Program Kit produces a complete, opinionated, usable baseline. Human attention is reserved for
deviations, material acknowledgements, and consequential decisions that cannot be answered safely
from the initial design or the selected Program Kit profile.

The absence of an explicit project choice is not a reason to leave an ordinary engineering choice
open when an applicable Program Kit default exists. Defaults are authoritative for the baseline but
remain easy to supersede through an explicit intake override or a later Accepted ADR.

## Decision precedence

Classify every bootstrap choice by the first applicable source:

1. **Explicit intake**: direct project intent such as "use PostgreSQL" or "Keycloak is the initial
   identity provider". Adopt it; do not reopen it merely because implementation details remain.
2. **Explicit override**: intake or project configuration deliberately replaces a Program Kit
   default. Record the default, override, reason, and affected evidence.
3. **Program Kit default**: apply the selected versioned profile when intake is silent.
4. **Derived default**: apply a low-risk consequence of accepted project shape and guardrails,
   recording the rationale and override path.
5. **Genuinely unresolved**: require human input only when business, legal, regulatory, security,
   financial, tenancy, production, or recovery context makes a safe default inappropriate.
6. **Deferred until triggered**: record decisions that are not yet material. They do not block
   unrelated specifications or implementation.

Words expressing commitment in an initial design (`must`, `uses`, `is`, `will`, `initial shape`)
are explicit intent. Examples, alternatives, future directions, and phrases such as `evaluate`,
`such as`, or `for example` remain candidates.

## Adoption evidence

Write `docs/architecture/bootstrap-decisions.json` using schema version `1.0`. It records the
versioned default profile, selected profiles, adopted choices and their sources, overrides,
material acknowledgements, genuinely unresolved decisions, and deferred decisions. Every adopted
choice includes a stable ID, decision, rationale, and easy override path.

The assessment human gate approves the exact hash of the assessment, tooling evaluation, decision
backlog, decision register, and concise review packet. Architecture may then treat explicit intake,
Program Kit defaults, and derived defaults as accepted bootstrap authority under the ratified
constitution. Consolidate them in `docs/architecture/decisions/bootstrap-baseline.md`; do not create
one approval chore per ordinary default.

Project-specific choices outside that reviewed baseline still require the normal ADR process.

## .NET default

When .NET is selected, `ProgramKit.Host` and the application-bundle model are the automatic runtime
default. Adopt them unless the initial design explicitly opts out. An opt-out records the alternate
host, reason, consequences, and affected managed baseline.

The standard runtime currently introduces pinned Program Kit, CShells, and Nuplane preview packages
and the configured preview package sources. The assessment review packet must disclose that material
supply-chain fact. Approving the assessment records the human acknowledgement; it does not download
packages or run restore. Repository synchronization and networked restore remain separate actions.

## Proportional decisions

Do not turn every valid question into an ADR or bootstrap blocker. Close ordinary details through
the applicable default, feature specification, acceptance criteria, or deterministic test. Defer
production topology, workload objectives, legal retention, and recovery objectives until their
lifecycle gates when they do not block the first vertical slice.

