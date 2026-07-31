# ProgramKit Development Tools — Implementation Plan 3.0 review

Canonical source:
`pkid:plan:program-kit:development-tools@2.0.0`

Canonical SHA-256:
`051f5ad4ce778b404707e9b9c94445c36677ffa235320c8aa3665b9445b53e56`

Bound design SHA-256:
`918db6923687e0098d2b5c59936714c4f804235dfa18299bd6d6830535c7d5cb`

This Markdown is a reviewer projection. The canonical JSON governs.

The work units are deliberately serial. Each unit rechecks current source truth
and the official contracts it affects. A material design deviation stops for
human review.

## Dependency order

```text
PKDT-W010 contracts/schemas/version topology/static gate
  -> PKDT-W020 Open Console mapping/policy/test fixture
  -> PKDT-W030 neutral MCP bridge
  -> PKDT-W040 registration ownership/lifecycle
  -> PKDT-W050 Codex writer and genuine cold proof
  -> PKDT-W060 Claude writer and external proof kit
  -> PKDT-W070 genuine Claude evidence and closure
```

## Work units

### `PKDT-W010` — contracts, schemas, versions, and gate binding

Extend `Orbyss.ProgramKit.Development` with the five exact 1.0.0 identities,
canonical models/validation, compatibility rules, and component/version
topology. Bind the already accepted private ProgramKit gate without changing
or extending it.

Allowed edits are the new Development Tools schemas, the existing Development
package, bounded version/component maps, schema registration, focused fixtures,
tests, docs, solution, and locks.

Stop on material accepted/current Console incompatibility, consumer semantics
in ProgramKit, unrepresentable version topology, or any need for a new/extended
gate.

### `PKDT-W020` — mapping, policy, and proof fixture

Implement complete Open Console mapping, default-all selection, exact-revision
exclusion, blocked reporting, structured projection, fail-closed policy, and
the minimal challenge fixture from exact locally prepared packages.

Stop on silent omission/weakening, inferred access or side effects,
non-canonical results, inability to report blocked selection, or ProgramKit
project/source/build-output coupling.

### `PKDT-W030` — provider-neutral MCP bridge

Create `Orbyss.ProgramKit.DevelopmentTools.Mcp` and
`program-kit-development-tools-mcp`. Prove MCP `2025-11-25` initialize/list/call,
structured results, exact-byte validation, clean stdout/stderr, fresh consumer
processes, timeout, cancellation races, concurrency, idempotency, and failure.

Stop on MCP drift, provider-specific runtime code, unbounded resources,
automatic retry, shared consumer state, provider calls, capability calls, or
nested loops.

### `PKDT-W040` — explicit registration lifecycle

Add deterministic proposal, exact digest acceptance, per-provider ownership
locks, atomic mutation, read-only status, explicit update diff, exact removal,
collision/path safety, and crash recovery to `program-kit`.

Stop if mutation precedes exact acceptance, ownership is ambiguous, unrelated
provider bytes can change, status mutates, writes are partial/uncontained, or a
registration command starts any process/provider/tool.

### `PKDT-W050` — Codex writer and genuine cold proof

Implement the exact owned `.codex/config.toml` entry and fixtures. Run genuine
isolated Codex sessions A/B/C, including semantic-only discovery/invocation,
permission denial, tamper/collision/update/remove cases, process isolation, and
session-C non-discovery.

Stop on material Codex contract drift, inherited path/command knowledge,
unisolated sessions, global/trust/permission mutation, surviving processes, or
non-genuine/incomplete evidence.

### `PKDT-W060` — Claude Code writer and external acceptance kit

Implement exact `.mcp.json` project-entry behavior and local lifecycle fixtures.
Prove it never writes `.claude/settings.json`, trust, server approval, or allow
permissions. Produce a deterministic evidence kit for the human to run on the
other machine from the exact same commit and neutral artifacts.

Stop on material Claude Code contract drift, permission/trust mutation, global
writes, hidden machine assumptions, non-deterministic kit bytes, or evidence
that cannot be validated without Claude installed locally.

### `PKDT-W070` — genuine Claude evidence and closure

Validate the returned genuine Claude A/B/C evidence, close all 32 acceptance
fixtures, run full repository/package/static conformance, and finish canonical
package/CLI/schema documentation and implementation evidence.

Stop and leave cross-provider acceptance open if the returned evidence is
missing, changed, fabricated, non-cold, secret-bearing, from different bytes,
or incomplete. Do not claim model/provider/general behavioral equivalence.

## Requirements

| ID | Observable outcome |
| --- | --- |
| `PKDT-R001` | Exact contract, schema, package, executable, and MCP identities are versioned and digest-bound. |
| `PKDT-R002` | Every Open Console operation is selected, exactly excluded, or selected-but-blocked; none is silently omitted. |
| `PKDT-R003` | Structured projection invokes one fresh consumer process and validates one canonical JSON result. |
| `PKDT-R004` | Side effects, resources, timeout, cancellation, concurrency, retry, and idempotency are fail-closed. |
| `PKDT-R005` | The consumer uses only exact locally prepared packages and controlled NuGet mapping. |
| `PKDT-R006` | Both providers use the same exact neutral MCP bridge. |
| `PKDT-R007` | Proposal/register/status/update/remove preserve exact ownership and human authority. |
| `PKDT-R008` | Codex owns only one reviewed project MCP entry. |
| `PKDT-R009` | Claude Code owns only one reviewed project MCP entry and no settings/trust/permission state. |
| `PKDT-R010` | Missing, tampered, incompatible, colliding, changed, or unowned bytes fail closed. |
| `PKDT-R011` | Both providers prove isolated A/B/C cold-session behavior. |
| `PKDT-R012` | The complete negative matrix has deterministic or genuine provider evidence. |
| `PKDT-R013` | Shared neutral digests match; provider observations remain labelled; closure waits for genuine Claude evidence. |
| `PKDT-R014` | No autonomous behavior exists and canonical documentation remains in ProgramKit. |
| `PKDT-R015` | Every change requires explicit reviewed update or migration/removal and fresh registration. |
| `PKDT-R016` | ProgramKit C# reuses the exact private gate and affected units recheck current Console source truth. |

## Approval boundary

Approval of this plan would authorize only `PKDT-W010` through `PKDT-W070`
against the exact canonical design and plan digests. Implementation remains
work-unit bounded and must stop on material architecture change.

It would not authorize Corrective Reconstruction, provider/global permission
changes, autonomous behavior, external repository edits, package publication,
release, deployment, or any deferred transport/provider.
