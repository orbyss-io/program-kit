# Canonical public-analyzer release-binding gate extension

Artifact identity:
`pkid:design:program-kit:canonical-public-analyzer-release-binding-gate@0.1.0-alpha.3`.

State: `ready-for-human-decision`.

This artifact extends, and does not replace, the existing Program Kit private
C# source-quality gate:

- gate policy
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`
  (`sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`);
- activation matrix
  `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`
  (`sha256:bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`);
- exhaustive verification profile
  `pkid:profile:program-kit:private-csharp-gate-exhaustive@1.0.0`
  (`sha256:80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d`).

The human-selected static-conformance disposition is `extend-existing`. No
new consumer-owned analyzer, private diagnostic family, hook, watcher, or
autonomous release mechanism is introduced.

## Static invariant allocation

| Invariant | Owner and layer | Enforcement |
| --- | --- | --- |
| Program Kit handwritten C# continues to satisfy private PKCS source policy. | Program Kit toolkit; Roslyn compiler | Reuse the exact existing private analyzer, selection lock, activation matrix, and exhaustive profile. |
| A compiler participation receipt proves the current invocation without changing compiled or portable-PDB bytes. | C# build-gate mechanics; MSBuild/compiler integration | Keep the unpredictable nonce only in the fresh invocation-root/evidence boundary. Generated receipt source, hint names, and compiler document paths are stable. The verifier accepts receipts only beneath the prepared invocation root. |
| Builds from two clean absolute roots produce the same first-party assembly bytes. | Build spine; executable conformance | Require explicit source-root path mapping and deterministic/CI compiler settings. A clean-root fixture compares SHA-256 for the public analyzer and one representative normal library before product units proceed. |
| Two clean packs of the same selected source produce identical nupkg bytes. | Release packaging; executable conformance | Use a pinned SDK with deterministic NuGet packing, one invariant ZIP-compatible timestamp, and one manifest-selected pack path. Compare every selected nupkg, not only the outer handoff archive. |
| The published public analyzer has one exact package digest, assembly digest, and explicit generated-output generator revisions. | Generated-source contract and release evidence; schema/model validation | Define one release-selection entry. For the affected host journey it carries `pkid:generator:program-kit:dotnet-host`; its digest is the SHA-256 of a canonical generator-revision descriptor, not the analyzer assembly digest. |
| The installed CLI can materialize that selection without Program Kit source or caller-invented data. | Command-line read projection; unit and cold-consumer conformance | Add one finite JSON command that reads the installed immutable release-selection catalog and emits a ready-to-embed analyzer component. Reject missing, duplicate, placeholder, or digest-inconsistent entries. |
| A declared generated-output generator revision is execution-linked. | Generated-output integrity and gate mechanics; executable conformance | The host materializer records the exact selected generator revision in deterministic output evidence, and gate verification requires it to equal one of the analyzer component's `receiptGeneratorRevisions`; a structurally valid but unobserved revision is rejected. |
| The release package set and GitHub publication use the same source of truth. | Release packaging; workflow conformance | The GitHub workflow invokes the manifest-selected packer, verifies deterministic repeat-pack evidence, uploads the exact package/checksum/selection manifests, and publishes no package outside that set. |
| Alpha.1 gate definitions have an explicit alpha.2 assessment path. | C# gate authoring; schema and command conformance | Validate against the named source and target schemas. Preserve canonical bytes when already conformant; otherwise fail with exact non-inventable artifact-selection decisions. |
| A package-only consumer completes describe/select, materialize, scaffold-lock, bind, and verify. | Consumer journey; isolated executable conformance | The cold proof installs only released candidate packages, selects the real public analyzer, supplies no internal digest, and checks positive and tamper paths. |

## Receipt mechanics

The random compilation nonce remains necessary to prove current execution, but
it is evidence, not product input:

1. `PrepareCSharpBuildGateTask` creates a fresh contained invocation root and
   nonce.
2. The nonce may select that root and appear in post-compile evidence.
3. Receipt generators emit constant canonical source at constant hint paths.
4. The generated-source output root is the fresh invocation root; stale or
   consumer-authored files outside it cannot satisfy verification.
5. The verifier checks the exact stable receipt marker beneath that root and
   binds the unpredictable nonce only into the external verification receipt.
6. Random values, machine paths, and current timestamps do not enter assemblies,
   PDBs, nupkgs, manifests, or release-selection JSON.

This applies to both the private Program Kit compiler receipt and the public
generated-source-contract compiler receipt, so Program Kit builds and opted-in
consumer builds retain deterministic output. These compiler-participation
receipts are not the `receiptGeneratorRevisions` list in a consumer gate
definition. That list identifies Program Kit output generators such as
`pkid:generator:program-kit:dotnet-host` and is bound through generated-output
evidence.

## Public analyzer selection

The canonical catalog contains an immutable row per published analyzer version:

```json
{
  "componentIdentity": "pkid:analyzer:program-kit:generated-source-contract",
  "semanticOwnerId": "pkid:domain:program-kit:generated-source-contract",
  "nugetPackageId": "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers",
  "packageAssetPath": "analyzers/dotnet/cs/Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.dll",
  "gateDefinitionFragment": {
    "artifact": {
      "kind": "analyzer-package",
      "repositoryRelativeProjectPath": null,
      "package": {
        "identity": "pkid:package:program-kit:orbyss-programkit-generatedsourcecontract-analyzers",
        "version": "0.1.0-alpha.3",
        "digest": "sha256:<exact-nupkg-digest>"
      },
      "assemblyFileName": "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.dll",
      "assemblyDigest": "sha256:<exact-assembly-digest>",
      "isPackable": true,
      "hasRuntimeAssets": false,
      "hasBuildTransitiveAssets": false
    },
    "receiptGeneratorRevisions": [
      {
        "identity": "pkid:generator:program-kit:dotnet-host",
        "version": "0.1.0-alpha.3",
        "digest": "sha256:<exact-generator-revision-descriptor-digest>"
      }
    ]
  }
}
```

The alpha.2 row is backfilled from the immutable NuGet package:

- nupkg:
  `sha256:282a10899e45c302cb0ba879b01f9ff6bf92bee0a73fd5c996ad77a4dee22a6c`;
- analyzer assembly:
  `sha256:7ec050ca9434657060b8e18400fc8d2db26424424e1840925abe383c4bc4e8e1`;
- dotnet-host generator revision: a frozen `0.1.0-alpha.2` descriptor derived
  from the exact alpha.2 release-tag generator source inventory; its own
  descriptor SHA-256 is emitted as the revision digest.

The historical GitHub handoff manifest is not a substitute for the NuGet
package digest: it records
`sha256:96cf2d7fd2cff80b4d10a00d11e2375318cec3639af89ed451070eb699e6b8b5`
for a different alpha.2 analyzer nupkg. The backfill therefore names NuGet.org
bytes explicitly, and alpha.3 qualification requires the GitHub evidence and
NuGet publication input to be the same file rather than two same-version packs.

The release packer derives the candidate alpha.3 row after the deterministic
analyzer package is finalized. It writes the catalog to transaction-local
output, includes it as installed CLI data without recompiling the CLI, and
publishes the same bytes as release evidence. This avoids a package
self-digest cycle.

The generator-revision descriptor follows the existing Program Kit convention
already used by `dotnet-configuration-provider`: the artifact reference digest
is the SHA-256 of the immutable descriptor bytes. Alpha.2 and alpha.3 have
separate descriptor rows. The descriptor contains the exact source tag/commit
and generator source inventory needed to justify the historical or candidate
revision. It is never inferred from the analyzer DLL, package ZIP metadata, or
the caller's gate definition.

The CLI command is:

```text
program-kit csharp-gate describe-public-analyzer-selection \
  --package-version 0.1.0-alpha.2 \
  --format json
```

It performs no network or source discovery. It reads the exact catalog shipped
with the installed CLI, selects exactly one version, validates internal digest
relationships, and emits canonical JSON containing the exact `artifact` and
`receiptGeneratorRevisions` fields suitable for the existing gate-definition
analyzer component.

## Interim alpha.2 consumer path

A consumer can update the package and assembly fields today using the two
NuGet.org values above. It may preserve its existing exact
`pkid:generator:program-kit:dotnet-host` reference only when the generated
output was not regenerated and still belongs to that same generator revision.
That is a narrow preservation path, not a newly derived alpha.2 value.

If the host output was regenerated, the existing reference is absent, or the
alpha.1 document does not satisfy the alpha.2 artifact-selection rules, there
is no supported complete workaround before the alpha.3 catalog exists. A
fabricated digest may pass today's shape-only definition validation, but it
does not establish generator provenance and must not be recommended.

## Finite activation and evidence

The existing private gate remains active for all current Program Kit
build/test/pack/publish project profiles. The extension adds establishment
evidence before product work:

1. same-root repeat assembly proof;
2. cross-root assembly proof;
3. repeat complete-package-set proof;
4. public-selection structural and digest proof;
5. generated-output generator-revision match and mismatch proof;
6. publish-workflow/manifest selection proof;
7. package-only consumer rebind proof.

Unknown package rows, package versions, analyzer assets, receipt identities,
timestamps, paths, or workflow selections fail closed. There are no temporary
exceptions and no self-renewal path.

## Establishment-first plan fragment

`PKRB-W010` is the sole `gate-establishment` unit. It adds the failing
conformance fixtures and the extended activation-evidence contract before any
product correction. `PKRB-W020` through `PKRB-W070` depend directly or
transitively on `PKRB-W010`. `PKRB-W080` closes only after the exact package
set, consumer journey, and private gate pass.

Implementation must stop for renewed design approval if it needs a new
analyzer, changes public PKCC diagnostic semantics, changes alpha.2 bytes,
uses an online lookup for selection, weakens the fresh-invocation trust
boundary, publishes a package, or cannot make every selected nupkg
byte-reproducible.

## Update and rollback

- Alpha.2 remains listed and immutable.
- Before publication, rollback is a normal branch revert; no external state
  exists.
- After approved alpha.3 publication, rollback means consumers select alpha.2;
  alpha.3 is never overwritten or silently rebuilt under the same version.
- A changed candidate byte requires a new deterministic evidence set before
  publication authority is requested.

This design grants no implementation or publication authority.
