# Program Kit integration and release provenance implementation plan

State: awaiting exact human approval.

The canonical `implementation-plan.json` has SHA-256
`082fae48f202e61943066e10f0293edb1d90b6428f3a43c162d1865e059f714c`.
It implements only canonical Architecture Design SHA-256
`50f31d1ab276c3597d9ac5e004a1657f94ad6fe062ee200615e2b56462ceacae`.

Approval of any other bytes does not authorize execution. A material change to
integration events, required outcomes, trust or authority boundaries, package
eligibility, no-rebuild publication, or approval-versus-execution semantics
requires a revised design and renewed human approval.

## Completion rules

- Complete the work as one reviewable Program Kit branch and pull request.
- Revalidate current `main`, the exact review artifacts and compatible
  execution bindings before implementation.
- Keep every work unit within its recorded allowed edits and stop conditions.
- Run focused verification during each unit and the complete exhaustive closure
  once in the final unit.
- Do not refresh the provider-local capability copy active in this task.
- Do not configure GitHub or NuGet, merge, publish packages, create a tag or
  release, or mutate another repository.
- Stop if current source is materially incompatible or any execution-resolved
  selection falls outside its approved identity and compatibility policy.

## Requirements

| ID | Required outcome |
| --- | --- |
| `PKIP-R001` | Repository CI owns the canonical integration entrypoint and shared result. |
| `PKIP-R002` | Pull requests verify GitHub's current synthetic combined source with read-only permissions. |
| `PKIP-R003` | The same stable check verifies merge groups on current `main`. |
| `PKIP-R004` | Workflow triggers, permissions, action pins, concurrency and required-check naming fail closed. |
| `PKIP-R005` | Only a successful trusted push to `main` creates a canonical coordinated package set. |
| `PKIP-R006` | Provenance and checksums close over source, workflow, profile, inventory and every package byte. |
| `PKIP-R007` | Human-dispatched publication consumes the selected prebuilt bytes without rebuilding. |
| `PKIP-R008` | Protected-environment approval and temporary trusted-publishing credentials remain late-bound and human-controlled. |
| `PKIP-R009` | Planning and capability contracts distinguish exact semantic approval from compatible exact execution evidence. |
| `PKIP-R010` | Provider-neutral guidance combines focused local work with shared CI evidence and real conflict resolution. |
| `PKIP-R011` | A finite handoff names every human-owned GitHub and NuGet setup action without claiming it is applied. |
| `PKIP-R012` | One Program Kit patch closes the complete source change while external activation remains separate. |

## Work units

### PKIP-W010 — Approval and execution bindings

Establish backward-readable Planning `0.1.0-alpha.5` support for
`approval-fixed` and `execution-resolved` bindings. Update design and
implementation capability semantics and their repository-owned delivery
artifacts without refreshing the capability copy active in this task.

Verify schema/model round trips, compatibility resolution, exact receipts,
historical readability, material-drift diagnostics and provider-neutral
capability packaging. Stop if compatible resolution can widen scope or
authority, overwrite historical approvals, or require a consumer CLI for
source contribution.

### PKIP-W020 — Integration and package-provenance operations

Depends on W010.

Add repository-backed operations that write and verify the closed
canonical-build record around the existing finite consumer-feed packer. Keep
the core deterministic and testable without GitHub secrets or publication
side effects.

Verify accepted evidence and tampered commit, workflow, profile, manifest,
inventory, size and digest cases. Stop if eligibility can be established by a
name alone, if package bytes can escape the checksum closure, or if verification
requires publication authority.

### PKIP-W030 — Required integration workflow

Depends on W020.

Add one least-privilege workflow for `pull_request`, `merge_group` and pushes to
`main`. A stable required-check job verifies combined source for all three
events; only a successful trusted `main` push proceeds to exhaustive package
creation, provenance closure, attestation and immutable artifact upload.

Pin official actions by commit, use event-aware concurrency and avoid path
filters that could leave a required check absent. Verify trigger, permission,
checkout, job-condition, package and failure topology. Stop if untrusted source
can receive secrets, write repository state or produce a publication candidate.

### PKIP-W040 — Protected no-rebuild publisher

Depends on W030.

Replace the current rebuild-and-publish workflow with a
`workflow_dispatch`-only publisher. Its input is one exact canonical-main run
ID. It verifies run and artifact eligibility and all internal package evidence
before entering the protected credential boundary, publishes the unchanged
package files, then creates matching durable release assets.

Verify rejected events, branches, commits, workflows, results, artifacts,
packages and tampering, plus the absence of restore/build/test/generate/pack.
Stop on ambiguous run selection, early authentication, arbitrary artifact
fallback, partial-publication concealment or tag/release mismatch.

### PKIP-W050 — Contributor and administration guidance

Depends on W040.

Document the provider-neutral contributor lifecycle and the exact human-owned
ruleset, merge-queue, protected-environment and trusted-publishing handoff.
Guidance preserves focused local checks and real conflict resolution while
letting contributors observe shared CI for whole-repository integration.

Stop if guidance lists provider brands, tells contributors to ignore directly
affected checks or conflicts, grants automation approval authority, or claims
external settings are already configured.

### PKIP-W060 — Single closure

Depends on W050 and is the plan's only closure work unit.

Run complete schema, capability, workflow, integration, tamper, documentation,
locked restore, full solution test, exhaustive private-gate and finite package
verification. Review the exact changed scope and close the one Program Kit
patch without external activation or publication.

Any failure, material design deviation, incompatible current source, unresolved
selection or need for new authority stops closure.

## Requirement trace

| Requirement | Work units |
| --- | --- |
| `PKIP-R001` | W020, W030, W060 |
| `PKIP-R002` | W030, W060 |
| `PKIP-R003` | W030, W050, W060 |
| `PKIP-R004` | W030, W040, W060 |
| `PKIP-R005` | W020, W030, W060 |
| `PKIP-R006` | W020, W030, W040, W060 |
| `PKIP-R007` | W040, W060 |
| `PKIP-R008` | W040, W050, W060 |
| `PKIP-R009` | W010, W020, W060 |
| `PKIP-R010` | W050, W060 |
| `PKIP-R011` | W050, W060 |
| `PKIP-R012` | W010, W020, W030, W040, W050, W060 |

## Static selection

The human selected `reuse-existing`. Every work unit binds the current private
C# gate activation matrix
`bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`
and exhaustive profile `1.0.1`,
`2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f`.
The exact review-candidate selection lock is
`8514e40a4ceea9c36772c0ee9a01d1e8ade481983250bbe74a69318912f5f279`.

During implementation, the new execution-binding contract will prevent a
compatible future profile-byte change from silently becoming new product
semantics. Its exact selected bytes will instead become trusted execution
evidence. Material incompatibility still stops.
