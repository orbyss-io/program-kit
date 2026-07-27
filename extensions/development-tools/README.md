# ProgramKit Development Tools review set

This is the replacement human-led review set for provider-neutral Development
Tools usable by fresh Codex and Claude Code sessions.

Review in this order:

1. `design-intent.md` — plain-language outcome, ownership, provider, safety,
   package-only, acceptance, and exclusion boundaries.
2. `convergence-notes.md` — the seven section-by-section human alignments and
   accepted static-conformance selection.
3. `architecture-design.json` — canonical Architecture Design `2.0.0`.
4. `architecture-design.md` — reviewer projection of the canonical design.
5. `static-conformance-disposition.json` — exact human-selected
   `reuse-existing` disposition.
6. `program-kit-private-gate-selection-lock.json` — exact private gate,
   activation, profile, evidence, scope, and source binding.
7. `provider-contract-evidence.json` — current official MCP, Codex, and Claude
   Code discovery/configuration/permission source findings.
8. `compatibility-version-matrix.json` — exact package, contract, schema,
   protocol, provider, update, and migration policy.
9. `acceptance-fixtures.json` — 32 prospective deterministic and genuine
   provider acceptance obligations.
10. `implementation-plan.json` — canonical Planning `3.0.0` plan with seven
    dependency-ordered work units.
11. `implementation-plan.md` — reviewer projection of the canonical plan.
12. `validation-report.md` — exact checks, unavailable operations, and
    canonical digests.
13. `review-manifest.json` — exact approval candidate and authority boundary.

`materialize-implementation-plan.ps1` deterministically rebuilds the canonical
plan from the current exact canonical design, provider evidence, disposition,
selection lock, and existing private-gate artifacts. It makes no runtime,
provider, configuration, or external-system changes.

No Development Tool contract, schema, MCP bridge, provider writer,
registration, permission, runtime operation, capability, or autonomous
behavior has been implemented by this review set.

Corrective Reconstruction remains on the backlog and is not part of this
approval candidate. The separate typed Console work is an independently
approved effort; Development Tools is host-profile-neutral and rechecks its
settled/current source truth at implementation preflight.

After validation and exact-digest approval, implementation may proceed only
through `implement-software-plan`, one bounded work unit at a time. A material
architecture change stops for renewed human review.
