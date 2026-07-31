# Canonical public-analyzer logical package-content implementation-plan amendment

Artifact identity:
`pkid:plan-amendment:program-kit:canonical-public-analyzer-logical-package-content@0.1.0-alpha.1`.

Implements only the exact Architecture Design amendment
`pkid:design-amendment:program-kit:canonical-public-analyzer-logical-package-content@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

The exact approved base plan
`pkid:plan:program-kit:canonical-public-analyzer-release-binding@0.1.0-alpha.3`
with SHA-256
`3b49633d6bfecd0894cef27b5f5baddc71bb02ad492e7084e65b2fb48d9ccc30`
remains authoritative except for the finite replacements below. Its serial
work-unit graph, allowed-edit boundaries, package selection, publication
prohibition, and unchanged `PKRB-W050` unit are preserved.

No work under this amendment is authorized until the human approves the exact
design-amendment and plan-amendment SHA-256 digests.

## Ordered work

| Unit | Amended outcome | Depends on |
| --- | --- | --- |
| `PKRB-W030` | Produce one manifest-selected unsigned candidate closure through SDK 10.0.302 with reproducible compiler outputs and logical package-content identities; record each exact candidate instance without requiring raw nupkg equality across independent packs. | `W020` |
| `PKRB-W040` | Preserve distinct run-scoped candidate, reproducible logical-content, assembly, generator, and repository-signed published identities in the release-selection catalog and finalizer. | `W030` |
| `PKRB-W050` | Unchanged loss-rejecting alpha.1-to-alpha.2 definition migration assessment/materialization. | `W010` |
| `PKRB-W060` | Adapt the existing immutable-artifact GitHub handoff to analyzer-first signature/content reconciliation and safe resumption, always publishing the selected exact attested candidate without rebuilding it. | `W030`, `W040` |
| `PKRB-W070` | Prove the package-only consumer journey against workflow-equivalent finalized packages and both exact-instance and logical-content tamper boundaries. | `W040`, `W050`, `W060` |
| `PKRB-W080` | Close compiler and logical package-content reproducibility, immutable-artifact publication conformance, signing/resumption simulation, and the manual workflow handoff without invoking publication. | `W070` |

No parallel implementation is authorized.

## Shared identity rules

Every affected unit uses these exact meanings:

- `candidatePackageSha256`: exact SHA-256 of one unsigned nupkg instance from
  the selected canonical-build run;
- `packageContentDigest`: deterministic digest of the validated logical
  non-signature package projection defined by the design amendment; and
- `publishedPackageSha256`: exact SHA-256 of the verified NuGet.org
  repository-signed nupkg.

No field substitutes for another. A candidate hash may differ across
independent packs with equal logical contents. One publication attempt must
retain and publish one exact candidate instance.

## `PKRB-W030` — logical package-content reproducibility

### Scope

1. Keep `global.json` and repository SDK declarations pinned to 10.0.302.
2. Keep the complete release-package manifest as the only package-set
   authority and include the consumer meta-package in that SDK-pack path.
3. Retain bounded ZIP safety validation, fixed-envelope writing where already
   useful, signature rejection for unsigned candidates, and exact ordinary
   entry preservation. Do not rewrite NuGet's OPC XML or generated part path
   merely to equalize raw candidate hashes.
4. Add the fail-closed logical package-content projection from the design:
   validate exactly one contained core-properties relationship and normalize
   only its relationship ID, target, and resolved physical part path for the
   digest projection.
5. Record exact candidate hash/length and stable logical-content digest for
   every selected package.
6. Make the two-root verifier compare assemblies, portable PDBs, package
   selection/dependency closure, all logical-content digests, and a semantic
   manifest projection. It must report, not conceal, per-run candidate hashes.
7. Require every observed raw-package difference to be attributable only to
   the validated OPC core-properties identity. Ordinary entry path or byte
   differences fail.

The base plan's W030 allowed-edit list remains unchanged.

### Verification

Run:

```powershell
pwsh -NoProfile -File build/Verify-ReproducibleConsumerFeed.ps1
```

Expected observation:

- two clean absolute roots produce identical selected analyzer and
  representative first-party assembly and portable-PDB digests;
- every package ID/version/role/dependency row and `packageContentDigest`
  agrees;
- each root's package manifest, checksum file, and provenance exactly match
  its own candidate instances;
- the semantic manifest projections agree;
- candidate hash differences, if present, are explicitly reported and their
  archive differences are limited to the validated OPC identity fields; and
- duplicate, unsafe, signature-bearing, malformed/multiple/external
  core-properties, ordinary-entry tamper, and over-broad normalization
  fixtures fail.

Run the exact base-plan activation matrix and synchronized exhaustive private
gate verification profile after the focused package tests.

### Stop conditions

Stop if:

- an assembly, portable PDB, NuSpec, dependency, payload, ordinary
  relationship, or logical-content digest differs across roots;
- the implementation ignores `_rels/.rels` wholesale or accepts more than the
  finite core-properties identity variance;
- an unsigned candidate contains a signature;
- any exact per-run candidate hash, manifest, checksum, or provenance claim is
  internally inaccurate;
- the meta-package remains on a second selection or pack path; or
- satisfying the projection requires another volatile-field exception.

## `PKRB-W040` — release-selection identity semantics

The base unit remains in force with these replacements:

1. Alpha.3 `candidatePackageSha256` is bound to the exact candidate instance
   selected for publication, not represented as an independently reproducible
   source property.
2. `packageContentDigest`, analyzer assembly digest, and generator descriptor
   digest remain deterministic and independently reproducible.
3. Catalog finalization still obtains `publishedPackageSha256` only from
   verified repository-signed bytes and still injects the final catalog without
   recompiling the CLI.
4. Tests must prove two different safe candidate instances with the same
   logical content cannot be conflated by exact-hash evidence, while the
   logical-content comparator recognizes only the finite allowed OPC variance.

Stop on any identity conflation, candidate substitution, self-digest cycle,
unverified published digest, or broader content exclusion.

## `PKRB-W050` — unchanged migration unit

`PKRB-W050` is byte-for-byte semantically unchanged from the base plan. It
retains its original inputs, allowed edits, verification, and stop conditions.

## `PKRB-W060` — immutable artifact and signed-content workflow convergence

### Scope

1. Reuse the established integrated-main pattern: pack once, close internal
   provenance, attest exact subjects, and upload one immutable canonical-build
   artifact.
2. Require the manual workflow to select an exact successful main run and
   artifact ID; verify its GitHub artifact digest, internal exact candidate
   hashes, source/workflow provenance, and attestations before publication.
3. Download and reverify the same exact artifact inside the protected publish
   job. Never pack again to recreate a candidate hash.
4. Preserve analyzer-first publication, repository-signature verification,
   bounded polling, final catalog injection without CLI recompilation, cold
   proof, remaining-package publication, and mismatch-safe resumption.
5. Compare candidate and repository-signed analyzer packages through the exact
   logical package-content projection after verifying the supported signature.
6. Persist candidate-instance, logical-content, and published-instance
   evidence distinctly in workflow artifacts and durable release assets.

The base W060 allowed-edit and publication-prohibition boundaries remain
unchanged.

### Verification

Workflow source-conformance and controlled phase simulations must prove:

- exact artifact-ID selection and digest verification;
- no pack or rebuild between selected candidate verification and its push;
- analyzer-first publish-or-verify behavior;
- repository-signature verification before logical-content comparison;
- acceptance of only the finite OPC relationship identity and supported
  signature difference;
- refusal of candidate substitution, ordinary-content mismatch, malformed OPC
  metadata, unsigned published bytes, and mismatched resumption;
- final catalog injection without assembly changes and cold proof before
  remaining pushes; and
- no workflow invocation or external mutation during implementation.

Stop on any fallback rebuild, artifact-name-only selection, missing
attestation/provenance check, over-broad content exclusion, hidden partial
publication, overwrite/rollback attempt, or implementation-time publication.

## `PKRB-W070` — package-only consumer proof

The base consumer journey remains unchanged. Extend its tamper matrix to prove:

- exact candidate evidence rejects a substituted unsigned nupkg even when its
  logical content agrees;
- logical-content evidence accepts only the validated OPC identity variance
  and supported repository signature transformation;
- payload, NuSpec, relationship, assembly, catalog, lock, generator-output,
  and signature tampering still fail; and
- the local controlled simulation and later human-started workflow invoke the
  same content comparator and cold-proof command.

The proof must not read the Program Kit checkout, use a fake analyzer, accept a
hand-supplied internal digest, mutate JTest, or contact NuGet during
implementation.

## `PKRB-W080` — final closure

Run the complete repository build, unit, conformance, exhaustive private-gate,
integration, package, determinism, workflow-conformance, controlled
signing/resumption, format, source-inventory, version-map, capability, and
package-only cold-consumer profiles required by the base plan.

The final clean-root package verification must establish:

- identical compiler outputs and complete logical package-content inventories;
- internally exact per-run candidate manifests, checksum files, provenance,
  and attestations or local attestation-equivalent evidence;
- explicitly reported raw candidate hashes with no assertion that independent
  packs reproduce them;
- archive differences limited to the finite validated OPC identity; and
- exact workflow reuse of the selected candidate instance without rebuilding.

The closure evidence reports the candidate commit, SDK, package-content
projection/profile identity and digest, every selected candidate/content
digest, workflow phase contract, accepted irreversible analyzer-first
boundary, and exact manual workflow input. It tells the human when the workflow
is ready but does not invoke it.

Stop on any failed profile, stale digest, unexplained package difference,
ordinary-content mismatch, missing exact-candidate evidence, branch drift,
workflow path that can rebuild or publish outside explicit human start, or a
need for actual publication to complete implementation verification.

## Static-conformance and approval boundary

Disposition: `extend-existing`.

The established private gate selection remains active and no new analyzer is
authorized. This amendment changes executable package evidence, not C# source
semantic ownership. Every changed C# file remains subject to the exact active
selection and synchronized exhaustive verification profile from the base plan.

Approval authorizes only the amended `PKRB-W030`, `PKRB-W040`, `PKRB-W060`,
`PKRB-W070`, and `PKRB-W080` semantics plus unchanged `PKRB-W050`. It does not
authorize publication, workflow invocation, package push, tag or release
creation, deployment, promotion, SDK installation, or unlisting alpha.2.

