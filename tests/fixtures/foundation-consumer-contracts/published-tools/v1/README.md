# Official Foundation tools compatibility, v1

This fixture answers whether the **published** `Orbyss.Foundation.Build` 0.1.0 and
`Orbyss.Foundation.OpenApi.Exporter` 0.2.4 can consume the new runtime contracts.
Source-built tools with those version strings do not supply this evidence. The validator restores
the official exporter from a public-only NuGet configuration and isolated cache, maps Build exactly
to nuget.org, and records the actual archive hashes and native restore provenance.

The two independent projects use only exact runtime PackageReferences. Core contains a semantic
collection model and has no feature descriptor. API owns the operation request/response projections,
strict request and bounded response metadata and their `ValueSequence` array shape. Public Build emits the source-bound schema-two
descriptor and must reject an unreviewed, compilable DTO change. The official exporter composes
the real feature closure, exports the typed contracts, binds all staged package/configuration/output
hashes, and must reject an incorrect producer version without writing output. Throwing storage and
hosted-initializer sentinels prove that cold metadata composition does not resolve operation storage
or start application initialization. The throwing data-source class is a fixture-only fault sentinel;
it performs no provider I/O and is not an application provider implementation.

Select runtime origin and version explicitly; no installed profile/default is selected:

```powershell
python tests/validate_foundation_published_tools.py --runtime-source private --runtime-version <exact-private-version> --packages <fresh-candidate-feed> --nuget-config <configured-preview-sources> --dotnet <SDK202-dotnet.exe>
python tests/validate_foundation_published_tools.py --runtime-source public --runtime-version <published-runtime-version> --nuget-config <configured-preview-sources> --dotnet <SDK202-dotnet.exe>
```

Private runs record `runtimePublished: false`. A public run accepts no private feed and additionally
checks listed/restorable metadata for its three runtime roots. Neither mode qualifies the complete
public dependency profile, published Host image, browser, settings-metadata companion or consumer
migration. No publication, default promotion, Release suite or paid worker is initiated. Runtime
closure restore disables SDK package pruning only in the generated deployment project, retaining
the selected-framework nuspec dependencies that native tooling must load.

The remaining PK2B sequence uses a new named public profile, materialized candidate catalog and a
new native lock/qualification recipe. Preserve every historical profile, receipt, recipe and lock.
The existing commands that accept an exact candidate profile can then run separately:

```powershell
python extensions/program-kit-building-blocks/scripts/public_availability.py --target . --catalog <materialized-candidate-catalog> --all --evidence <new-availability-evidence>
python tests/validate_published_forms_browser.py --profile <new-profile> --engines chromium,webkit
python tests/validate_bootstrap_runtime.py --profile <new-profile>
```

The browser command requires `PROGRAM_KIT_NPM_TOKEN` in its owning invocation; credential use
remains confined to the existing redacted availability/restore processes. Host acceptance verifies
and pulls the exact published OCI digest, then exercises activation/replacement, HTTP/OpenAPI and
restart. Firefox remains a tagged CI gate. Run the new generic publisher activation/composition
recipe with its own inspected native lock before constructing its portable qualification receipt.
The old `validate_default_dependency_profile.py` always copies the historical 0.2.4 lock, and the
old receipt builder binds that historical recipe/lock; those bytes cannot establish a new profile.
Registering/selecting a qualified default follows all availability/closure/behavior gates and the
separately owned release decision. These commands prepare reviewable evidence only.
