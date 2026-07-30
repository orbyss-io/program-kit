# Canonical public-analyzer release-binding implementation plan

Canonical source:
`implementation-plan.json`

Canonical SHA-256:
`0821ef64266769c79e68b5754a585ca9452aa6eb2b44e2b0668c50ae20fe88e5`

State: amended and ready for human decision. `PKRB-W010` and `PKRB-W020`
are complete; `PKRB-W030` through `PKRB-W080` require renewed approval.

## Ordered work

| Unit | Outcome | Depends on |
| --- | --- | --- |
| `PKRB-W010` | Establish the extended private gate, selection lock, activation evidence, and controlled negative fixtures before product changes. | None |
| `PKRB-W020` | Make compiler participation receipts and path mapping stable across invocations and source roots. | `W010` |
| `PKRB-W030` | Produce one byte-reproducible, manifest-selected unsigned candidate nupkg closure through the pinned 10.0.302 SDK and repository-owned canonical writer, including the consumer meta-package. | `W020` |
| `PKRB-W040` | Add immutable dotnet-host descriptors, execution-linked output evidence, alpha.2 published selection, alpha.3 candidate/content evidence, the publication-time catalog finalizer, and installed CLI projection. | `W030` |
| `PKRB-W050` | Add a loss-rejecting alpha.1-to-alpha.2 definition migration assessment/materialization path. | `W010` |
| `PKRB-W060` | Make GitHub Actions use one analyzer-first, repository-signature-verifying, content-equivalence-checking, catalog-finalizing, cold-verifying, and mismatch-safe resumable publication path—without invoking it during implementation. | `W030`, `W040` |
| `PKRB-W070` | Prove a package-only consumer can describe, migrate/materialize, scaffold-lock, bind, and verify the real alpha.2 and workflow-equivalent finalized alpha.3 selections; the workflow reruns the proof against actual signed alpha.3 bytes. | `W040`, `W050`, `W060` |
| `PKRB-W080` | Run full candidate and controlled signing/resumption closure verification and hand the exact human-started GitHub workflow boundary to the human. | `W070` |

No parallel implementation groups are authorized. Every product and closure
unit passes through the establishment-first gate and final closure.
The completed `PKRB-W010` and `PKRB-W020` units retain their exact originally
approved architecture-design input digest. The current plan traces `PKRB-W010`
to the amended gate-design digest, while accepting its existing establishment
evidence because the enforcement allocation and controlled fixture categories
are unchanged. Only `PKRB-W030` through `PKRB-W080` perform amended product or
closure work.

## Completion standard

The completed candidate must demonstrate:

- identical analyzer DLL, portable PDB, canonical unsigned candidate nupkg,
  package-content, manifest, and checksum digests across clean roots;
- exact alpha.2 installed catalog data and deterministic alpha.3
  candidate/content/assembly/generator evidence;
- controlled proof that verified repository-signed bytes finalize a
  ready-to-embed CLI selection without recompiling the CLI;
- generated-output evidence that matches the declared dotnet-host revision;
- a documented, loss-rejecting alpha.1 schema transition;
- identical local and workflow candidate selection plus explicit
  analyzer-first, repository-signature/content verification, repeat-pack,
  cold-proof, remaining-package, and safe-resumption phases;
- a cold consumer rebind with no Program Kit checkout, local feed, fake
  analyzer, or hand-supplied internal digest;
- full tests and private-gate verification.

The final unit reports the candidate commit, canonicalization profile,
candidate/content evidence, workflow phase contract, accepted irreversible
analyzer-first boundary, and exact digests, then tells the human that the
GitHub workflow is ready. It does not invoke that workflow. The exact
NuGet.org-signed alpha.3 package digest and final installed alpha.3 catalog are
created and verified only inside that later human-started workflow.
