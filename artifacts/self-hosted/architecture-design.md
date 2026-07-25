# Orbyss Program Kit self-hosted baseline

Canonical source: `pkid:design:program-kit:self-hosted-baseline@1.0.0`

Source digest: `sha256:c5ed7f0d4f278181f138dd5a4dcb9300502dd85aea8be7271c7da15762439327`

## Intent

Describe the implemented Program Kit packages, dependency direction,
governance boundaries, and deterministic projections through the architecture
contract supplied by Program Kit itself.

## Historical authority

The approved bootstrap design
`pkid:design:program-kit:baseline@0.3.0#sha256:dbe65ea112a172761f5725c210add00867b8b9f7a180a8b5ee6f80e42dace1c9`
remains historical source truth. This projection neither replaces that source
nor claims retroactive capability authorship.

## Package inventory

| Package | Role | Direct Program Kit dependencies |
| --- | --- | --- |
| `Artifacts` | universal artifact contracts | none |
| `Architecture` | architecture contracts and validators | Artifacts |
| `Quality` | quality contracts and validators | Artifacts |
| `Planning` | plans and approvals | Artifacts, Quality |
| `Development` | routing and receipts | Artifacts, Planning |
| `Serialization.JSON` | JSON mechanics and canonicalization | Artifacts |
| `Workbench` | deterministic tooling operations | Architecture, Artifacts, Development, Planning, Quality, Serialization.JSON |
| `Modularity` | modularity contracts | Artifacts |
| `Modularity.InProcess` | in-process modularity provider | Modularity |
| `Tasks.Core` | runtime-independent task contracts | Artifacts |
| `Tasks` | task composition and coordination | Modularity, Tasks.Core |
| `Tasks.InProcess` | volatile task provider | Tasks |
| `Tasks.Hosting` | Generic Host bridge | Tasks |
| `Tasks.Schedules` | provider-neutral schedule semantics | Tasks.Core |
| `Tasks.Schedules.Cronos` | optional Cronos provider | Tasks.Schedules |
| `DotNet` | .NET generation and local publication | Architecture, Planning, Quality, Serialization.JSON, Tasks, Tasks.Core, Tasks.Schedules, Workbench |
| `CommandLine` | scriptable host | DotNet, Workbench |
| `CapabilityBundle` | exact content-only capability package | none |

Every package is version `0.1.0-alpha.1`.

## Reference policy

- Declared inward project and package edges are allowed.
- Runtime and contract projects may not reference `.agents` capabilities,
  `.codex` wrappers, or development-session procedure code.
- The capability bundle is content-only and does not make capability procedures
  runtime dependencies.

## Authority and history

Only explicit human evidence grants design or implementation authority.
Development receipts report actual events; they do not approve work. The
self-hosted plan is a separate, non-authoritative representation of `PK-W080`,
while the exact bootstrap plan and approval remain controlling history.

## Projection policy

This Markdown is intentionally lossy and regenerable. The canonical JSON design
is authoritative for exact fields, identifiers, boundaries, scenarios, and
status claims.
