# Optional team delivery

The extension is installed with Program Kit but disabled by default. No credentials, provider
calls or cloud writes occur during installation, upgrade, profile preparation or content checks.
Core architecture, specification intake and technical governance remain mandatory.

`delivery.schema.json` is the product v1 contract for profiles, bindings, history and normalized
work. `azure-default.json` proposes Agile Epic → Feature → User Story → optional Task mappings.
`github-default.json` proposes existing native Feature/Task types and explicit Epic/Requirement
label mappings pending capability discovery. Both contain clearly named setup placeholders.
Field names, role identities and resource mappings require later provider verification. Board
status is progress, never proof of refinement readiness, implementation admission or acceptance.

The shared profile owns authority/type/field/state meanings and policy. A consumer-owned
`.program-kit/delivery/binding.json` pins its source repository, immutable commit, path and
exact-byte digest plus a local snapshot. It supplies repository/team identity, permitted defaults,
artifact paths and local-entry → Requirement/optional Task bindings. A profile contains semantic
identity and policy, not its own Git hash. Commit a colocated profile before its binding.

`.program-kit/delivery/history.json` retains accepted activation, profile-change and disconnect
records. Each record links the previous record digest and the selected binding/profile digest.
These files live outside installed extension content and caches. Missing/malformed records,
changed digests, or changed committed history require recovery. Git history helps detect ordinary
file deletion; shallow/offline history cannot prove absence of removed provenance. These controls
coordinate cooperating consumers; they do not protect against rewriting all repository history.

Preparation writes a `prepared` configuration with empty history. Its authority remains local.
Actual enabled activation requires provider verification and an accepted activation record.
The Azure command implements reviewed setup, planning and per-repository activation for refinement;
read [azure-planning.md](azure-planning.md) for its scope and recovery rules. GitHub activation,
implementation claims, verified delivery and acceptance admission are not available yet. A fabricated
capability flag, native board column or local Ready/Delivered text cannot enable those operations.
No machine-local override can select a different delivery binding or bypass the core gate.

Draft epics need only title, outcome and business owner; empty optional fields/arrays/nulls in the
normalized envelope are bookkeeping, not extra intake questions. Refinement adds scope, exclusions,
architecture prerequisites and observable acceptance. Implementation also requires an accountable
executor, current accepted business/artifact basis, dependency/coordination assessment and verification
plan. Content validation does not prove the referenced artifacts exist, that prose is sound, or
that a provider currently admits the work. Core checks and later provider admission supply that.

Each technical entry has one primary Requirement. Cross-repository independent execution uses
meaningful child Tasks with the parent's accepted basis. Simple work can be executed directly on
the Requirement. The approved decomposition excludes simultaneous parent-wide and child claims;
the accountable owner need not monopolize implementation. Runtime claims arrive in Phase 4.

Platform owns business intent, acceptance, priority, assignment, dependencies, milestone and delivery
state. Git owns technical plans, architecture and code. Local roadmap views in enabled mode are
explicit projections; editing them cannot change cloud authority. Verified delivery needs current
evidence, while business acceptance is a separate attributable decision.
