# Program Kit consumer CLI journey completeness implementation plan

Artifact identity:
`pkid:plan:program-kit:consumer-cli-journey-completeness@0.1.0-alpha.1`.

Design:
`pkid:design:program-kit:consumer-cli-journey-completeness@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

This digest-bound transitional plan contains exactly one atomic implementation
work unit. It does not instantiate the legacy Implementation Plan `3.0.0`
contract or silently amend the approved PKAV artifact.

## `PKCJ-W010` Complete the package-only consumer CLI journey

Required outcome: a clean consumer installs only the exact Program Kit
`0.1.0-alpha.2` CLI package closure and, without a Program Kit checkout,
retrieves complete capabilities/resources/schemas, initializes either or both
providers, materializes a canonical gate definition without reverse
engineering, and invokes the packaged Console generator.

Depends on: committed `PKAV-W040` at
`5273297c666f958840ad0279853fb305349f5571`.

Atomicity: all product changes and the complete cold-consumer proof land in one
commit. No partial package is offered to JTest. If one required behavior cannot
be closed without material redesign, stop the whole work unit.

Allowed edits:

- `src/Orbyss.ProgramKit.CommandLine/` for finite descriptors/help, packaged
  payload ownership, capability/schema/resource retrieval, transactional
  initialization, gate materialization, diagnostics, and deterministic output;
- existing schema modules and bounded Workbench/C# gate contract/authoring
  services required for exact cataloging and canonical materialization;
- `.agent-capabilities/` distributable definitions, adapter templates,
  supporting resources, manifest, and generated catalog projections;
- `src/Orbyss.ProgramKit.CapabilityBundle/` only to preserve the internal
  exact-byte build/verification artifact from the same canonical source;
- `schemas/csharp-build-gates/` for immutable alpha.2 gate-definition schema
  and exact alpha.1 migration;
- package metadata, manifest/lock projections, and README/package README
  commands affected by the exact alpha.2 candidate bytes;
- focused unit/conformance fixtures plus one isolated cold-consumer proof
  script that starts only from packed artifacts;
- this extension's validation/report/manifest artifacts after implementation.

Implementation obligations:

1. Enrich the one finite descriptor catalog so parsing and generated help share
   paths, descriptions, argument names, required options, allowed values,
   examples, and exit behavior.
2. Implement no-argument, `--help`, and command-path help without routing or
   authority semantics. Make invalid finite values and argument-count errors
   enumerate the exact expected contract.
3. Pack the verified five-capability payload, adapters, and supporting
   resources inside the CLI from the canonical source tree; retain the
   CapabilityBundle only as a non-required internal verification artifact.
4. Remove `--program-kit-root` from the public consumer initializer. Resolve
   payload bytes relative to the exact installed CLI, reject the Program Kit
   authoring marker, preflight every change, and atomically write wrappers and
   the new lock.
5. Replace last-provider ownership with an ordinal multi-provider lock that
   records exact CLI, bundle, manifest, capability, template, wrapper, resource,
   digest, and path evidence. Preserve verified other-provider wrappers.
6. Migrate exact legacy locks only through explicit initialization; refuse
   modified/unowned collisions and leave no partial state.
7. Generate thin Codex and Claude wrappers that call
   `program-kit capabilities read <capability-id> --workspace-root .` and
   contain no source pointer or copied procedure.
8. Implement exact `capabilities read` and `read-resource` with installed
   version, payload, lock, provider, wrapper, and item verification. Emit only
   requested bytes on standard output; diagnostics use standard error.
9. Update canonical capabilities to use exact CLI-addressable resource/schema
   IDs and the approved alpha design-flow contracts. Recalculate all wrapper,
   payload, and catalog digests together. This consumes the consumer-delivery
   overlap with planned `PKAV-W050`; do not implement that overlap again.
10. Project the explicit schema modules into one duplicate-rejecting catalog.
    Implement offline `schemas list` and allow-listed `schemas read`, including
    exact identity/version/URI/digest/dependency metadata.
11. Add the exact C# gate authoring catalog and
    `csharp-gate describe-definition`; bind the packaged public analyzer
    package/assembly/rule/compatibility selections rather than discovering
    them from assemblies or feeds.
12. Add immutable gate-definition schema `0.1.0-alpha.2`, conditional
    local/package artifact rules, and an explicit deterministic alpha.1
    migration. Preserve alpha.1 bytes.
13. Implement `csharp-gate materialize-definition`: tolerate one UTF-8 BOM at
    draft ingestion, reject invalid encodings/duplicates, aggregate actionable
    schema and semantic diagnostics, stable-sort by documented keys, and write
    canonical BOM-free bytes. Never invent human or semantic values.
14. Make existing gate validation diagnostics state exact expected shapes or
    allowed values and eliminate hidden input-order trial and error.
15. Add deterministic one-line setup success output for initialize/refresh and
    verification operations without contaminating content-result standard
    output.
16. Update root and CLI package READMEs with exact alpha.2 local-feed
    install/initialize/help/schema/capability/gate journeys and Codex/Claude
    alternatives. Do not claim feed publication or automatic initialization.
17. Add unit and scenario conformance for help, provider discovery,
    multi-provider refresh, payload tamper/staleness, exact retrieval, schema
    closure, alpha gate migration/materialization, BOM, ordering, diagnostic
    aggregation, authoring denial, and all negative lock/ownership cases.
18. Pack all coordinated alpha.2 packages and run an isolated tool-path test
    from a flat local feed and isolated NuGet cache. The consumer fixture must
    contain no source checkout/project reference and must initialize/read
    Codex+Claude, materialize/validate a gate definition, and generate a real
    Console host.
19. Inspect package contents and dependency closure, emit exact package/asset
    SHA-256 evidence, run build/unit/routine/exhaustive profiles, and prove
    historical approval/closure bytes remain unchanged.
20. Commit and push the one completed work unit, then create one downloadable
    alpha.2 flat-feed ZIP plus checksum and the exact JTest retry prompt. Do not
    publish a package or create a GitHub Release.

Compatibility:

- Existing operational command paths remain stable.
- Consumer initialization intentionally removes the source-root dependency and
  migrates exact legacy ownership only through explicit refresh.
- Gate-definition alpha.1 is immutable and migrates to alpha.2; new canonical
  materialization emits alpha.2.
- All coordinated packages remain `0.1.0-alpha.2` because no alpha.2 archive or
  release has yet been declared final. One final byte set is handed to JTest.
- Capability definition and wrapper digest changes are explicit and
  transactionally refreshed.

Verification:

- locked restore only when dependency state requires it;
- mandatory Program Kit private C# gate through a no-restore Release build;
- all unit tests through the native MSTest runner;
- routine and exhaustive conformance profiles;
- exact capability/payload/schema/package archive inspection;
- isolated local-feed/tool-path/NuGet-cache cold-consumer proof;
- repeated initialization/read/materialization byte-idempotence;
- changed/staged scope review and immutable historical-evidence audit.

Stop conditions:

- any consumer operation still needs a Program Kit checkout, separate
  CapabilityBundle install, source-relative capability path, arbitrary URI,
  assembly grep, feed scan, or ambient first-party cache;
- help/resource/schema/gate catalogs drift from their finite canonical source;
- a command grants authority, invents gate semantics, or hides a required human
  decision;
- initialization or refresh can partially mutate ownership state;
- one installed version can serve bytes to a differently locked workspace;
- gate materialization loses or invents a semantic value;
- alpha.1 immutable contract bytes change;
- the package-installed Console path cannot generate and seal a real host;
- any required build, unit, routine, exhaustive, package, or cold-consumer
  proof fails;
- implementation requires GitHub Release creation, feed publication, JTest
  mutation, or another material design deviation.

Completion:

Push one implementation commit and report it. Provide the final downloadable
alpha.2 package ZIP, SHA-256/checksum evidence, and JTest prompt in this task.
