# Historical exporter 0.2.3 adoption investigation

This report preserves the initial public 0.2.3 failure and its draft investigation.
Statements below about the unchanged VERSION and the 0.2.3 proposal describe that
historical snapshot. The current candidate is Program Kit 0.12.6 with a private
corrected exporter 0.2.4; it is not published or fully qualified for release.
Current migration requirements are maintained in
[migration-0.12.6](../releases/migration-0.12.6.md). Public 0.2.3 remains a negative
Assurance regression case, and historical receipts retain their original scope.

No new Program Kit release has been published for this change. The public release
remains 0.12.5. VERSION and published release assets are unchanged. The changes
on `codex/exporter-0.2.3` are a draft; their catalog pin does not establish consumer
compatibility or implementation readiness.

## Draft maintained upgrade

The proposed catalog advances only `Orbyss.Foundation.OpenApi.Exporter` to 0.2.3,
with an explicit `families.foundation.toolVersions` pin. Foundation runtime and
analyzer packages, the host, Forms and Localization retain their accepted pins.
Runtime packages must still match their exact family release. Tool overrides
must name actual NuGet dotnet tools; both their declarations and package versions
are bound by the resolution hash. The catalog resolution revision advances to 3.

The existing `--accept-openapi-producer-pin-reconciliation` updater option admits
only this complete exporter-only resolution change. Other package, activation,
source, configuration or composition changes retain the reviewed Draft transition
requirement. It verifies the prior accepted selection and applied lock before
installation, archives the original catalog/selection/architecture/lock bytes,
and uses the maintained resolver's Draft acceptance operation with the same
accepted decision IDs, rationale, scopes, targets and instances. The selection
revision and catalog binding advance; repository sync owns current materialization.
An interrupted catalog installation can resume only from the preserved exact
prior catalog. Existing version and stale-lock checks remain active.

Registered producer contracts and associated exporter planning pins reconcile
through the existing atomic helper. Runtime and unrelated package pins on the
same planning lines remain unchanged. Original planning and lifecycle bytes are
archived, historical reports remain intact, and after-tasks readiness is invalidated.

The maintained package target now packs identical consumer metadata at both
`program-kit/feature.json` and the producer's required
`orbyss-foundation/feature.json`. This retains the native release-closure contract
and supplies the actual exporter metadata without patching any packed archive.

## Actual native qualification

Testing used an isolated copy of De Zaaglijst. Its source selection, architecture
map and producer contract hashes remained unchanged. No source-consumer upgrade,
architecture acceptance, worker or feature implementation was performed.

The real sequential updater stopped before component installation:
`PKB405 host-bff-interop compatibility tooling changed; renew the proof`.
This historical proof was preserved rather than treated as a current proof.

For the separate producer qualification, the maintained .NET synchronizer applied
the template to the copy and the maintained reconciliation helper updated its
producer contract/planning and invalidated stale readiness. The native pipeline
script remained byte-identical to the maintained template. The selected SDK,
Node, npm and oasdiff were actually resolved to 10.0.202, 24.20.0, 11.19.0 and
1.29.1. The tool manifest restored the public exporter 0.2.3 without an exporter
override or a version-check bypass.

The first export exposed missing consumer descriptors. After the maintained
packing correction, `dotnet pack DeZaaglijst.slnx -c Release -p:Version=0.1.0`
compiled and packed the actual consumer projects. Native `release_bundle.py stage`
validated the real package closure. The three consumer feature packages contained
byte-identical descriptor aliases. Re-running the unmodified native pipeline then
failed solely with:

```text
PKO200 activated features have no unique staged package descriptor: Orbyss.Foundation.Authentication.Assurance
PKO205 OpenAPI export for de-zaaglijst-private-v1 failed with exit code 2.
```

No successful native pipeline receipt, normalized artifact, compatibility result,
generated TypeScript or TypeScript application compilation was manufactured.
The pipeline stops before those stages. The initial-baseline option applies only
to the disposable qualification copy and created no baseline because export failed.

## Foundation package assessment

The public exporter nupkg identifies publisher commit
`3c4da01641550e3031cb9baed3354364d0f56b95` and SHA-256
`c8b1f441546bb88da816a0a4e5ab1ea88ecd3a97ae0d89633f15aa2bfa35638e`.
Its actual version admission succeeded. The publisher's
[PackageSet loader](https://github.com/orbyss-io/dotnet-foundation/blob/3c4da01641550e3031cb9baed3354364d0f56b95/src/Orbyss.Foundation.OpenApi.Exporter/PackageSet.cs)
reads `orbyss-foundation/feature.json`; its
[built-in feature definitions](https://github.com/orbyss-io/dotnet-foundation/blob/3c4da01641550e3031cb9baed3354364d0f56b95/src/Orbyss.Foundation.OpenApi.Exporter/BuiltInFeatures.cs)
omit Authentication.Assurance. The staged public Assurance 0.2.2 package has no
descriptor. The independently downloaded public Assurance 0.2.3 package also has
no producer descriptor; its SHA-256 is
`e512f837c8889cf3c250ad0443931f1ee510587308c6bd257740dbaae38cc1cb`.
Changing its version alone cannot supply the missing descriptor. A blanket
Foundation family upgrade is therefore not a demonstrated fix.

The publisher must supply supported Assurance descriptor/activation handling in
a public immutable package. Preserve this consumer's selected Assurance feature.
Then qualify actual export, normalization, oasdiff, TypeScript generation and
consumer compilation, including producer mismatch rejection. Renew stale consumer
proofs through their maintained lifecycle. The separate installed architecture
checker defects remain in the consumer's
`.program-kit/proposals/architecture-managed-inputs/README.md`; this change does
not repair or waive them.

## Evidence and publication

Local evidence is preserved under `artifacts/exporter-adoption/`:
`qualification.json`, `upgrade.log`, `dotnet-sync.log`,
`native-pipeline-initialize.log`, `native-pack.log`, `native-stage.log`,
`native-pipeline-repacked.log`, `development.log` and targeted upgrade logs.
`qualification.json` records public package hashes, the unchanged native pipeline
hash, source-consumer authority hashes and actual newly packed consumer hashes.

Publication is blocked by producer qualification. Once qualification succeeds,
prepare a new coherent Program Kit version, run fresh local Release validation in
the user's terminal under AGENTS.md, inspect its preserved log/receipt/hashes, and
require green current CI and successful tagged Release before claiming availability.
Retain Firefox in CI; the known local Windows Firefox limitation remains unchanged.
