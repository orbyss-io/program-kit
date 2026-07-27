# ProgramKit Development Tools implementation plan

Human-readable projection of
`pkid:plan:program-kit:development-tools@1.0.0`.

Canonical plan SHA-256:
`3b44ee514087fc6934a094766453434f9e9d0f6f04f84d909438fe2eb4752e85`.
Canonical design:
`pkid:design:program-kit:development-tools@1.0.0#sha256:6ec7ac36df528e838ec2423d6f2bf3838e27b31edd93f5c09a66c3730b1f44b2`.
The canonical JSON plan is authoritative.

## Dependency order

1. `PKDT-W010` — versioned Development Tool manifest, registration lock,
   evidence, serialization, validation, compatibility, and migrations.
2. `PKDT-W020` — exact generated Console proof package/executable and direct
   provider-neutral, package-only conformance.
3. `PKDT-W030` — re-check official provider contracts, then implement the one
   thin stable-MCP stdio Codex adapter.
4. `PKDT-W040` — explicit collision-safe project registration, verification,
   update, and removal with exact ownership locking.
5. `PKDT-W050` — genuine cold-session discovery/invocation, negative fixtures,
   canonical documentation, evidence, and bounded closure.

All work units are serial. No runtime, adapter, or registration work may be
started under design authority. After exact approval, each work unit must be
implemented through the registered `implement-software-plan` provider and
verified before the next begins. Material architecture or provider-contract
deviation stops for human review.

## Requirement coverage

| Requirements | Work units | Acceptance focus |
|---|---|---|
| `PKDT-R001`–`R003` | W010–W030 | Identity, JSON/exit semantics, access, side effects, execution policy |
| `PKDT-R004`–`R005` | W020, W030, W050 | Current Console proof and package-only consumption |
| `PKDT-R006`–`R007` | W030, W040 | Exact thin MCP adapter and authoritative provider drift gate |
| `PKDT-R008`–`R009` | W030–W050 | Owned registration lifecycle and no autonomous authority |
| `PKDT-R010`–`R011` | W050 | Cold discovery plus complete negative evidence |
| `PKDT-R012` | W020–W050 | Canonical documentation and explicit deferrals |

## Required verification

W010, W030, and W040 run focused unit/conformance validation over exact schemas,
messages, byte locks, TOML preservation, process mapping, permissions, and
lifecycle failures. W020 proves exact prepared-package construction and rejects
all ProgramKit source/build coupling. W050 runs the full locked solution tests
plus cold sessions A, B, and post-removal non-discovery.

The fixture catalog in `acceptance-fixtures.json` is required, not illustrative.
Closure evidence must bind exact fixture ids, package/contract/adapter/lock
digests, provider revision, process/session boundary, result classification, and
redacted observation.

## Stop boundary

Approval does not authorize provider-native transport, plugins, remote MCP,
additional providers, AI/provider calls from the tool, capabilities, autonomous
behavior, feed publication, release, deployment, website authority, or a
material deviation from the exact design or plan.
