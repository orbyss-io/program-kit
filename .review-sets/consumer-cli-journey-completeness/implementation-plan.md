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

Required outcome: a clean supported consumer installs only the exact Program
Kit `0.1.0-alpha.2` CLI package closure and, without a Program Kit checkout,
preflights and retrieves every consumer capability's complete read-only
knowledge closure, initializes either or both providers at the correct trigger
boundary, materializes a canonical gate definition without reverse
engineering, and invokes the packaged Console generator.

Depends on: committed `PKAV-W040` at
`5273297c666f958840ad0279853fb305349f5571`.

Atomicity: all product changes and the complete cold-consumer proof land in one
commit. No partial package is offered to JTest. If one required behavior cannot
be closed without material redesign, stop the whole work unit.

Allowed edits:

- `src/Orbyss.ProgramKit.CommandLine/` for finite descriptors/help, packaged
  payload ownership, capability knowledge-closure/readiness, command/schema/
  resource retrieval, transactional initialization, gate materialization,
  diagnostics, and deterministic output;
- existing schema modules and bounded Workbench/C# gate contract/authoring
  services required for exact cataloging and canonical materialization;
- existing stable Program Kit diagnostic catalogs and bounded artifact
  validation composition required for read-only explanation/inspection;
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
3. Define one versioned `CapabilityKnowledgeClosure` contract and release
   catalog that separate consumer, contributor-only, and unavailable roles and
   bind every command, schema dependency, resource, template, catalog, example,
   migration, diagnostic/remediation, package selection, and required external
   or human input for each consumer capability.
4. Mechanically validate every Program Kit reference in each canonical
   consumer capability against its declared transitive closure. Reject partial,
   duplicate, stale, circular, implicit source-relative, or unregistered
   knowledge.
5. Pack the verified six-capability consumer payload, closure manifests,
   adapters, and supporting resources as embedded read-only CLI resources from
   the canonical source tree; retain the
   CapabilityBundle only as a non-required internal verification artifact.
6. Include `publish-dotnet-application-locally` as a consumer capability;
   classify `author-and-maintain-skills` as contributor-only and the three
   future release flows as unavailable. A consumer-available catalog row is
   invalid unless its complete closure is retrievable.
7. Remove `--program-kit-root` from the public consumer initializer. Resolve
   payload bytes relative to the exact installed CLI, reject the Program Kit
   authoring marker, preflight every change, and atomically write wrappers and
   the new lock.
8. Replace last-provider ownership with an ordinal multi-provider lock that
   records exact CLI, bundle, manifest, capability, template, wrapper, resource,
   digest, and path evidence. Preserve verified other-provider wrappers.
9. Migrate exact legacy locks only through explicit initialization; refuse
   modified/unowned collisions and leave no partial state.
10. Generate thin Codex and Claude wrappers that preflight then call
    `program-kit capabilities read <capability-id> --workspace-root .`; contain
    no source pointer or copied procedure; and have trigger metadata bound to
    the one canonical precedence table.
11. Implement exact `capabilities catalog`, `preflight`, `read`, and
    `read-resource`. Keep availability, active-provider registration, and
    complete-closure freshness structurally separate. Emit only requested bytes
    on content-result standard output; diagnostics use standard error.
12. Permit `read` only after `preflight` is `ready`. Exact installed version,
    embedded payload, complete transitive closure, lock, provider, and wrapper
    must verify; reads never repair state.
13. Update canonical capabilities to use exact CLI-addressable resource/schema
   IDs and the approved alpha design-flow contracts. Recalculate all wrapper,
   payload, and catalog digests together. This consumes the consumer-delivery
   overlap with planned `PKAV-W050`; do not implement that overlap again.
14. Project the explicit schema modules into one duplicate-rejecting catalog.
    Implement offline `schemas list` and allow-listed `schemas read`, including
    exact identity/version/URI/digest/dependency metadata.
15. Add `commands describe` from the same finite descriptor source used by
    parser/help, including allowed values, authority, input/output, examples,
    and diagnostic contracts.
16. Define one exact troubleshooting resource and include it in every
    capability closure that can invoke validation, build, generation, refresh,
    package, or publication behavior.
17. Implement `diagnostics explain` over finite registered Program Kit
    diagnostic/remediation entries. Bind owner, meaning, affected contract,
    expected evidence, likely owned causes, bounded remediation, stop
    condition, and related command/schema identities. External or unknown IDs
    must never receive invented Program Kit remediation.
18. Implement read-only `artifacts inspect` over one explicit artifact and the
    embedded registered schema/semantic validators. Report exact identity,
    validation, command, and capability ownership without writing,
    normalizing, migrating, repairing, or approving the artifact.
19. Add the exact C# gate authoring catalog and
    `csharp-gate describe-definition`; bind the packaged public analyzer
    package/assembly/rule/compatibility selections rather than discovering
    them from assemblies or feeds.
20. Add immutable gate-definition schema `0.1.0-alpha.2`, conditional
    local/package artifact rules, and an explicit deterministic alpha.1
    migration. Preserve alpha.1 bytes.
21. Implement `csharp-gate materialize-definition`: tolerate one UTF-8 BOM at
    draft ingestion, reject invalid encodings/duplicates, aggregate actionable
    schema and semantic diagnostics, stable-sort by documented keys, and write
    canonical BOM-free bytes. Never invent human or semantic values.
22. Make existing gate validation diagnostics state exact expected shapes or
    allowed values and eliminate hidden input-order trial and error.
23. Add deterministic one-line setup success output for initialize/refresh and
    verification operations without contaminating content-result standard
    output.
24. Make the canonical knowledge surface read-only: no CLI knowledge mutation
    or workspace export, no canonical knowledge files in the consumer
    workspace, embedded-resource validation for operations, and refusal after
    wrapper/payload/lock tampering. Document that OS-level read-only
    installation is required to resist a malicious same-user executable edit.
25. Update root and CLI package READMEs with exact alpha.2 local-feed
    install/initialize/help/schema/capability/gate journeys and Codex/Claude
    alternatives. Do not claim feed publication or automatic initialization.
26. Add unit and scenario conformance for help, provider discovery,
    multi-provider refresh, payload tamper/staleness, exact retrieval, schema
    closure, alpha gate migration/materialization, BOM, ordering, diagnostic
    aggregation, authoring denial, and all negative lock/ownership cases.
27. Add diagnostic/interpretation conformance proving every Program Kit ID has
    exact remediation metadata, external/unknown IDs do not hallucinate
    ownership, and artifact inspection never changes input bytes.
28. Add fresh Codex and Claude journey fixtures for ordinary read-only work,
    direct maintenance, direct design/convergence, exact implementation,
    explicit gate design, explicit local publication, vague routing,
    unavailable release, post-completion work, and next-day continuation.
29. Pack all coordinated alpha.2 packages and run an isolated tool-path test
    from a flat local feed and isolated NuGet cache. The consumer fixture must
    contain no source checkout/project reference and must initialize/read
    Codex+Claude, materialize/validate a gate definition, and generate a real
    Console host.
30. Prove all six capabilities and every closure item can be read at exact
    bytes; contributor/unavailable/partial/stale closures fail closed; no
    canonical file is materialized; redirected copies cannot influence
    validation; and wrapper edits invalidate preflight/read.
31. Reproduce build/validation/interpretation failures through the installed
    CLI and prove the active capability can retrieve the exact command,
    diagnostic, artifact, schema, and remediation knowledge without source
    checkout or assembly inspection.
32. Inspect package contents and dependency closure, emit exact package/asset
    SHA-256 evidence, run build/unit/routine/exhaustive profiles, and prove
    historical approval/closure bytes remain unchanged.
33. Commit and push the one completed work unit, then create one downloadable
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
- The consumer payload contains every available consumer-role capability;
  contributor-only and unavailable identities remain catalog-visible but
  non-retrievable.

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
- any consumer capability is marked ready with a missing, stale, undeclared,
  or unverified product-owned knowledge dependency;
- any Program Kit diagnostic lacks exact ownership/evidence/remediation/stop
  metadata, or an external/unknown failure receives invented remediation;
- artifact interpretation mutates, normalizes, repairs, or consumes a
  non-embedded schema as canonical;
- any CLI operation can mutate canonical knowledge or validation can consume a
  redirected consumer copy as canonical;
- any claim implies protection against a malicious same-user process without
  an external read-only installation boundary;
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
