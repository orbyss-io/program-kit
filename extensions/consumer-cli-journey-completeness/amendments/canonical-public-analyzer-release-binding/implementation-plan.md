# Canonical public-analyzer release-binding implementation plan

Canonical source:
`implementation-plan.json`

Canonical SHA-256:
`6735e42bb93d6c18ada00e0961fdb645f07864e9629c6a663e757a10b9020f3d`

State: ready for human decision. Work has not started.

## Ordered work

| Unit | Outcome | Depends on |
| --- | --- | --- |
| `PKRB-W010` | Establish the extended private gate, selection lock, activation evidence, and controlled negative fixtures before product changes. | None |
| `PKRB-W020` | Make compiler participation receipts and path mapping stable across invocations and source roots. | `W010` |
| `PKRB-W030` | Produce one deterministic, manifest-selected complete nupkg closure including the consumer meta-package. | `W020` |
| `PKRB-W040` | Add immutable dotnet-host revision descriptors, execution-linked output evidence, the installed analyzer-selection catalog, and its CLI projection. | `W030` |
| `PKRB-W050` | Add a loss-rejecting alpha.1-to-alpha.2 definition migration assessment/materialization path. | `W010` |
| `PKRB-W060` | Make GitHub Actions consume the exact local qualification pack and evidence outputs without publishing. | `W030`, `W040` |
| `PKRB-W070` | Prove a package-only consumer can describe, migrate/materialize, scaffold-lock, bind, and verify the real analyzer. | `W040`, `W050`, `W060` |
| `PKRB-W080` | Run full closure verification and hand the exact alpha.3 candidate to the human for a separate publication decision. | `W070` |

No parallel implementation groups are authorized. Every product and closure
unit passes through the establishment-first gate and final closure.

## Completion standard

The completed candidate must demonstrate:

- identical analyzer DLL and complete nupkg-set digests across clean roots;
- exact alpha.2 and alpha.3 installed catalog rows;
- a ready-to-embed CLI selection with package, assembly, and generator-revision
  digests;
- generated-output evidence that matches the declared dotnet-host revision;
- a documented, loss-rejecting alpha.1 schema transition;
- identical local and workflow package/evidence selection;
- a cold consumer rebind with no Program Kit checkout, local feed, fake
  analyzer, or hand-supplied internal digest;
- full tests and private-gate verification.

The final unit reports the candidate commit and evidence digests and tells the
human that the GitHub workflow is ready. It does not invoke that workflow.
