# Program Kit operation exposure and application capabilities — implementation plan

Status: candidate review projection. The canonical source is
`implementation-plan.json`; implementation remains `not-started`.

The plan contains eleven bounded work units. It deliberately separates the
operation/MCP/registration path from the capability-bundle path and joins them
only at the explicit workspace lifecycle.

## Dependency order

```text
PKDT-W010 Operation catalog and exposure bindings
  ├─ PKDT-W020 Generated Console/API projection and introspection
  │    └─ PKDT-W030 Dual-era neutral MCP bridge
  │          └─ PKDT-W040 Explicit tool-registration lifecycle
  └─ PKDT-W050 Application outcome-capability contracts
       └─ PKDT-W060 Acquisition, verification, and immutable store

PKDT-W040 + PKDT-W060
  └─ PKDT-W070 Capability lifecycle, locks, provider projections, flat catalog
       └─ PKDT-W080 Program Kit package-only dogfood
            └─ PKDT-W090 Deterministic and package-only acceptance
                 ├─ PKDT-W100 Genuine Codex acceptance
                 └──────────────┐
PKDT-W090 ───────────────────────┴─ PKDT-W110 Claude/cross-provider closure
```

## Work units

### PKDT-W010 — operation contracts

Generalize the implemented operation contracts into one host-neutral
`OperationContractCatalog` with explicit exposure bindings. Preserve operation
identity/revision across Console and OpenAPI hosts and bind all implementation
to the exact current `reuse-existing` Program Kit gate. Do not edit or reinterpret
the completed health-patching extension.

### PKDT-W020 — generated hosts and introspection

Project generated Console and API hosts mechanically. Add the reserved,
non-executing structured Console introspection document for the complete catalog
or one exact operation and refuse every reserved-token collision.

### PKDT-W030 — MCP bridge

Implement one provider-neutral stdio bridge for current modern and legacy MCP
discovery plus exact `tools/list` and `tools/call`. Prove direct operation use
without a capability and preserve application-owned result/failure semantics.

### PKDT-W040 — tool registration

Implement deterministic project-scoped proposal, exact human acceptance,
provider ownership locks, status, update, and removal. Keep registration,
provider trust/permission, and invocation separate. Never start a provider,
server, or application.

### PKDT-W050 — application capability contracts

Define the optional deterministic descriptor, procedure, exact operation/schema
bindings, finite knowledge closure, readiness, explicit handoff, publisher
attestation, and authoring safeguard. Reject prose-only or mechanically
one-per-command bundles.

### PKDT-W060 — acquisition and storage

Generalize the existing bundle engine for explicit public local directory, zip,
NuGet, HTTPS, and GitHub-release source kinds. Normalize every carrier into one
verified immutable content-addressed representation. Private/authenticated
acquisition remains deferred.

### PKDT-W070 — explicit capability lifecycle

Implement deterministic initialize proposal and acceptance, per-bundle/provider
locks, refresh, update, status, removal, preflight, reads, pruning, provider
projections, and one atomic flat workspace catalog.

Refresh repairs derived bytes from unchanged trusted inputs. Update alone can
accept a changed authoritative bundle. A changed lock is never adopted.

### PKDT-W080 — Program Kit dogfood

Package Program Kit consumer capabilities through the same generic application
bundle, verifier, locks, provider projections, catalog, lifecycle, and
cold-session rules. Prove package-only outcome parity without source knowledge.

### PKDT-W090 — deterministic acceptance

Run the reviewed 42-fixture matrix: host parity, introspection, modern/legacy
MCP, direct MCP without a capability, explicit registration and initialization,
closure refusal, multi-source acquisition, catalog drift/refresh/update,
JTest-shaped outcome guidance, Program Kit dogfood, and no-autonomy negatives.

### PKDT-W100 — genuine Codex acceptance

Use exact reviewed packages in isolated fresh Codex sessions to prove native
tool/capability selection, direct operation use, guided outcome use, project
trust/approval boundaries, changed-byte refusal/update, refresh repair, exact
removal, and later non-discovery.

### PKDT-W110 — Claude and closure

Validate genuine returned Claude Code evidence against exact reviewed bytes,
then close the cross-provider, package-only, static-gate, authority, no-autonomy,
publisher/conformance, documentation, and changed-file-scope evidence.

## Verification and stops

Every unit runs the current Program Kit private gate and full solution tests in
addition to focused tests. Provider-facing units must recheck the exact current
official provider contracts before implementation. Any material protocol,
authority, package-boundary, semantic-ownership, health-task, or static-gate
deviation stops the implementing flow for new human design approval.

Closure remains open if genuine Claude Code evidence is unavailable or does not
match the exact reviewed package, lock, and capability bytes.

## Authority boundary

Approval of this plan would authorize only the exact bounded implementation
represented by canonical design and plan digests. It would not authorize
provider trust/permission, user-global writes, application semantic approval,
private feed/authentication work, publication, release, deployment, external
repository mutation, or any autonomous behavior.
