# Application handoff execution journal

2026-10-06. Source: `087290b7d3fc3f6abf5b2460e94b1d3af367ec31`, branch
`codex/human-infrastructure-handoff`. Work is confined to this worktree and disposable fixtures.
The four saved design/inventory/example/plan files were untracked; preserved. No other initial changes.

- Read AGENTS.md and all saved handoff documents. No Release, publication, tags or workers authorized.
- Stable identity uses consumer-owned `eng/application-handoff.json`; new release descriptions require
  an explicit ID. Historical descriptors remain schema version 1 and readable without that input.
- Read committed Foundation source at `30db6759e75bc53f7cc457e19c5a9d77297b9e71` with per-command
  safe-directory/excludes overrides. No Foundation files or original checkout changed.
- Foundation `src/Orbyss.Foundation.Authentication/FoundationWebOptions.cs` and
  `FoundationWebOptionsValidator.cs` expose types/defaults/validation; no supported offline settings
  metadata export was found in committed `src/`. These classes alone do not establish binding,
  precedence, reload and complete host/CShells/Nuplane coverage. W3 remains externally incomplete.
  Required upstream deliverable: publisher-owned, version-bound offline metadata for supported
  host, shell, Nuplane and selected feature options, including source/default/validation semantics,
  secrets, binding precedence and reload behavior, without initialization or service access.
- Retain the exact selected catalog through existing dependency-profile rendering; install the
  canonical public-availability verifier bytes under eng/. Lock remains the selection authority.

Implementation and validation results follow below.

- A Codex archive removed the requested worktree during startup (snapshot 1367742945d226b8f7b7c2daa98df6a47a368208).
  Recovered its exact four uncommitted documents; recreated an independent checkout at the requested
  path/branch and baseline. Original repository used only as a read-only object source; no original
  checkout, branch, index or dirty file changed. No extra snapshot differences.

- User requires notice/approval before Foundation edits. No such edits were made. Pragmatic proposal:
  additive publisher-owned versioned settings metadata in the existing Foundation build/package
  pipeline, emitted per owning package and bound to its exact version. Validate against actual typed
  defaults/validators/binding behavior. Do not use a generic reflection API or OpenAPI service
  registration to derive configuration contracts. The latter builds a WebApplication and calls
  feature ConfigureServices. CShells/Nuplane metadata needs explicit ownership/coverage. Recheck
  the authoritative Foundation source with its concurrent owner before any separately authorized
  implementation; inspected local HEAD may predate the published baseline. Proposed shape is the
  Program Kit settings-metadata schema (subject to upstream agreement), not a claimed existing API.

- Copied only generated pinned SDK/schema/analyzer caches from original artifacts into isolated
  artifacts. No dirty source, docs, Foundation contract work or original checkout state imported.
- Scaffold regression uncovered legacy OpenAPI inline migration rejecting modern contract-path
  registries emitted by openapi_init.py/openapi_pipeline.py. Corrected migration to preserve native
  path references; unsupported entry types still reject. Legacy inline transforms retain their gate.

## Implementation completed in Program Kit

- W1: explicit identity input/migration diagnostics; bundle descriptor schema version 1 remains
  unchanged. Existing released identities (including readable historical folder IDs) retain meaning.
- W2: consumer-owned docs/application/ guides and declaration preserved through repeated sync;
  affected guide/runtime/settings/contracts maintenance routed through existing feature guidance.
- W3: application-owned source-backed metadata schema/assembly and real typed fixture export;
  required owner/scope omissions block ready assembly. Framework coverage remains open.
- W4: deterministic receiver index/archive/checksum, portable verifier and format schemas; actual
  descriptor member references (canonical/legacy), bundle/package/API/source integrity, explicit
  applicability/bindings, secret/path/archive checks, and publisher-required API coverage.
- W5: exact selected catalog retained through dependency_profile.py; canonical availability verifier
  copied byte-for-byte from its single maintained source into eng/. Its profile-only import remains
  outside consumer lock mode; the consumer release uses no installed extension/catalog. Exact host
  evidence matching has a retained native verifier. Existing gates and ordering stay authoritative.
  CI delivers engineering/contract inputs; final release delivers/attests runtime and receiver outputs.

## Validation and corrections

- Initial bundle/scaffold/availability checks passed before broader acceptance refinements.
- Final handoff acceptance: 9 tests passed, covering source-generated two-API HTTP examples and typed
  settings parity, multiple component bindings to a shared package, current/historical identity,
  deterministic independent receiver consumption, missing/tampered/stale/unresolved/conflicting
  inputs, secret/path/archive rejection, required publisher API coverage and absent framework scopes.
- Scaffold/toolkit-removal regression uncovered the legacy inline OpenAPI migration rejecting modern
  path registries. Fixed without rewriting those references; invalid entry types remain rejected.
- First targeted batch: handoff 8, generated schemas, scaffold, build contract, availability,
  exporter-upgrade, dependency profiles and targeted managed/OpenAPI/feature-closure checks passed.
  Two failures: source-freshness diagnostic precedence differed from historical sourceConfiguration
  diagnostics; nested disposable docs deletion used an old root-parent assertion. Preserved the
  old diagnostic order and checked resolved containment for the nested path. Both now pass.
- Fixed incidental Windows-default decoding of original UTF-8 test text; unrelated text restored.
- Final native .NET fixture actually restores/builds/tests/packs and invokes native contract/bundle/
  handoff commands after toolkit removal. Wrong domain behavior still rejects. It correctly emits
  incomplete status for missing framework metadata. See artifacts/standalone-engineering/result.json.
- The HTTP fixture's package descriptors/pipeline receipts are synthetic assembly inputs, not
  Foundation exporter or live host qualification. Its endpoint behavior, contracts and settings
  exporter are real application source, tested independently. No complete framework coverage claim.
- First bounded Development passed; final review added FeatureDescriptor requiresContractCoverage
  enforcement and portable schema/engineering distribution. Rechecked handoff (9 pass) and reran
  bounded Development on those final changes. Final run: 70/70 checks pass,
  chromium,webkit, journal artifacts/validation-runs/20261006T103312Z-d43c382c/journal.json.
  Initial run is preserved at artifacts/validation-runs/20261006T102554Z-c5ca532d/. No Release receipt.
- Supplementary bundle diagnostic/migration rerun: 15 tests passed, saved as
  artifacts/handoff-validation/validate_release_bundle-rerun.log. Final handoff log:
  artifacts/handoff-validation/validate_application_handoff-final.log. Initial targeted logs/results
  stay preserved. A trailing blank line was removed after validation (formatting only).

## FeatureDescriptor assessment and external dependency

Existing FeatureDescriptors are reused rather than replaced. Committed Foundation Build schema and
DescriptorContract support package/feature identity, dependencies, routes, dormant/composition/
contract-coverage flags, configured route-prefix references and source hashes. The locally cached
Orbyss.Foundation.Build 0.1.0 package was also inspected: schemas/feature.schema.json covers schema 1
feature facts with additionalProperties:false and contains no settings contract. The committed newer
schema 1/2 also has no supported-setting semantics. This is scoped inspected evidence, not a claim
about uninspected branches/packages. Recheck the authoritative source with its concurrent owner.

Preferred upstream direction: extend existing publisher build/package metadata with a small
version-bound settings companion, sharing real declarations/defaults and qualification tests; retain
FeatureDescriptors as feature authority and existing descriptor compatibility. No runtime reflection
or service-registration API is necessary just to read that metadata. The exact contract/version and
Foundation versus CShells/Nuplane integration ownership must be agreed; the Program Kit metadata
shape is an assembly proposal, not a claimed existing Foundation API. W3 stays incomplete until real
publisher coverage and source/package binding are implemented and qualified. User requires notice
before Foundation changes; no Foundation, real consumer or original checkout change was made.
No publication, tags, paid workers, interactive intake/bootstrap or complete Release suite run.

## Follow-on authorization (2026-10-06)

The user requested a commit/push of this validated handoff branch first and agreed to the
publisher-owned settings companion recommendation. Foundation follow-on implementation is now
authorized within that scope, after inspecting its authoritative source and preserving concurrent
work. This authorizes no publication, stable tag, real-consumer change, paid worker or Release run.

