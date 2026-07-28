# Program Kit alpha version transition validation

## Result

The transitional review set is structurally valid, internally digest-bound, and
ready for one exact human design-and-plan decision. It remains unapproved and no
implementation was performed.

Validation used Program Kit source at
`773d7cf3859fe98c2fd72139872312994effeb8d`.

## Canonical contract validation

The review validator compiled a temporary local adapter directly against the
already-built Program Kit assemblies and invoked
`JsonSchemaWorkbenchValidator`. It performed no package restore, feed access, or
network access. The temporary files were removed after validation.

Passed:

- `architecture-design.json` against
  `pkid:schema:program-kit:architecture-design@2.0.0`,
  digest
  `sha256:2698ce65a29cb0d5007b2ab1773d7e387385df7c8b72495804b292b6af696198`;
- `implementation-plan.json` against
  `pkid:schema:program-kit:implementation-plan@3.0.0`,
  digest
  `sha256:0f3b8f524b29ec7b5871ce411f06852e1b06326a5e1da616184627df0b5ea1b6`;
  and
- `static-conformance-disposition.json` against
  `pkid:schema:program-kit:static-conformance-disposition@1.0.0`,
  digest
  `sha256:834902de4706a7c6859390bd7ee5e4fd6a3e7e455486348c02a1cb84604d15bd`.

These current contract versions are intentional transitional inputs. The plan
establishes Architecture Design `0.1.0-alpha.2`, Implementation Plan
`0.1.0-alpha.3`, and StaticConformanceDisposition `0.1.0-alpha.1` before the
separate health review is authored.

## Targeted semantic validation

Passed:

- exact human-intent, static-design-basis, decision-source, disposition,
  selection-lock, design, and plan digest bindings;
- preservation of the exact human statement
  `i approve all recommendations and fixes` without treating it as approval of
  later-produced canonical bytes;
- one unblocked `reuse-existing` static disposition selecting
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`;
- exact private activation matrix, exhaustive verification profile, and
  materialized reusable-gate closure evidence;
- 14 unique requirements, seven unique work units, dependency order, exact
  requirement trace, and closure reachability from `PKAV-W070` to every product
  unit;
- explicit compatibility, stop, verification, activation-matrix, and
  verification-profile bindings on every work unit;
- five version intents, protected external/history/fixture boundaries, the
  `0.1.0-alpha.2` product release boundary, and the deferred Release Kit stable
  policy;
- explicit non-goals for JTest mutation and source-capability activation in the
  Program Kit authoring workspace; and
- current-format review status `scaffolded`,
  `ready-for-human-decision`, `awaiting-human-approval`, and
  `implementationStatus: not-started` without overclaiming approval or
  implementation.

## Projection and byte validation

Passed:

- UTF-8 without byte-order marks and LF-only line endings for every review
  artifact;
- JSON syntax for every JSON artifact;
- exact canonical design and plan digests in the deterministic Markdown
  projections;
- two consecutive materializer runs with byte-identical
  `implementation-plan.json`, `architecture-design.md`, and
  `implementation-plan.md`; and
- exact repository-file SHA-256 values for every artifact listed by the final
  review manifest.

## Deliberately not performed

- No Program Kit implementation or runtime source was changed.
- No package was built for release, published, promoted, signed, or deployed.
- No capability was initialized or activated in this authoring workspace.
- No consumer or JTest repository was inspected or mutated.
- The full Program Kit build and test suites were not used to claim
  implementation conformance; those are mandatory work-unit and closure checks
  after exact approval.
- No stable patch/minor/major progression policy was selected. Release Kit owns
  that future decision.

## Reproduction

From the Program Kit repository root:

```powershell
& 'extensions/alpha-version-transition/materialize-review-set.ps1'
& 'extensions/alpha-version-transition/validate-review-set.ps1'
```

The validator creates only a bounded temporary compiler output beneath the
system temporary directory and removes it after schema validation.
