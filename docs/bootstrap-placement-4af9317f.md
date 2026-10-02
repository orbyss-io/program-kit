# Architecture placement failure in consumer run 4af9317f

This is historical **0.11.0** consumer evidence, not an unresolved placement-contract
defect in the published **0.12.1** release. Its tag commit
`73aad97d9b5238708c27623c3c00d6edec8b86d9` already publishes the executable schema,
hashed stage projection and shell/host guidance described below. The shipping change
is narrowed to worker permissions and related lifecycle retry guidance. The frozen
0.11.0 tooling candidate remains a separate optional recovery artifact; it has not
been installed in the original consumer.

Program Kit 0.11.0's installed `building_blocks.py::validate_placements` rejects
`deploy/PolicyApplication/Shells/policy-application.json` with PKB303 because the
case-insensitive basename must be **shells.json** for `cshell-shell`. The browser
target has the same rule. Each also requires `shell`, the runtime identity inside
the document, independently of the selection target ID. The rule applies to
planned targets without requiring files or scaffolding.

The installed 0.11.0 host-image check accepts a case-insensitive basename of
**Dockerfile** or one beginning **Dockerfile.**. Its existing
`deploy/PolicyApplication/Dockerfile` target satisfies that rule. A host DLL,
arbitrary image JSON, or `hostsettings.json` would fail the historical validator.
Generic repository-relative path validity is an additional prerequisite; it does
not replace the target-kind rules, owner linkage, ADR hashes or scope bindings.

The original worker context and selection schema did not publish the filename
rule. The worker correctly recorded BLOCKED, and the next native validator failed.
Spec Kit marks a command dispatch completed on process exit 0; it does not establish
that the architecture artifact contract succeeded. Do not advance its review gate,
mark the run completed, or reinterpret the structural failure as a transport error.

## Source correction and historical compatibility

The newer repository source already owns executable conventions in
`building-block-selection.schema.json#$defs/targetKindPlacement`. The resolver
consumes those rules and the bootstrap projection publishes the same definitions
and schema hash before drafting. Published 0.12.1 architecture guidance already
names `shells.json` and its runtime identity; existing placement tests cover legal
planned targets, invalid shell filenames and host forms. A producer that ignores
that published contract can still receive PKB303; that alone is not the 0.11.0 bug.

The current host-image model is **hostsettings.json**, a consumer configuration
binding the externally published Foundation image to an application release bundle.
Tests cover that legal planned target and reject Dockerfile, Dockerfile.production,
host DLL and incorrectly cased HostSettings.json targets. This is a runtime model
change made after 0.11.0, not a mechanical repair for this failed run. Do not copy
current catalog/package pins or silently rename the historical host target. A
whole-version upgrade also requires a reviewed saved-workflow migration; the
current lifecycle does not authorize a direct 0.11.0-to-0.12.2 migration.

The historical tooling candidate's early diagnostic asks for a version-matched
contract repair. Its recovery snapshots available partial outputs, acceptance scope and every
map-referenced ADR, in addition to inputs, state, log and review authority. It
refreshes only derived DSL/context, and reports the lifecycle retry command.
That retry regenerates the producer, validates outputs and retains human gates;
running a separate producer first would cause a redundant dispatch.

## Preserved evidence and offline replay

Evidence is under `artifacts/bootstrap-placement-4af9317f/`: `manifest.json`
binds the source snapshot and five version-matched tooling changes;
`verification.json` records original-validator/schema agreement for both shell
paths and the host conventions. The copy-only replay passed installation
coherence, architecture recovery and all five structural checks. Full stage
validation still failed on missing `docs/architecture/README.md`. This deliberately
does not claim narrative completion or approval.

While inspecting, the original consumer's Draft changed independently: both shell
paths now end in `shells.json`, and its refreshed context includes a filename hint.
The failed state and inactive lifecycle remained. This investigation did not edit
the original consumer. Its current partial work is preserved in the snapshot;
the replay verified that Draft documents, ADRs, canonical map, confirmed intake,
approved assessment, constitution and original workflow records stayed byte-for-byte
unchanged during recovery and structural validation. All replay dispatches are
deterministic tools; no coding agent was launched.

## Safe continuation for the original 0.11.0 run

A local, version-matched tooling candidate is prepared at
`artifacts/bootstrap-placement-4af9317f/candidate/extensions/`. It keeps original
0.11.0 extension manifests, catalog, runtime pins, workflow and Dockerfile host
semantics. It adds executable schema rules matching the installed validator,
projects their hash before drafting, publishes worker guidance, preserves partial
Draft recovery evidence, and backports invocation-scoped workspace-write dispatch.
The original resolver is unchanged. Both extensions were successfully reinstalled
through Spec Kit in the disposable copy, and installation/recovery/structural
checks passed again afterward. This is a local tooling repair, not a published
0.11.0 package or an application upgrade.

The historical installation predates the newer shared diagnostic modules. The
policy backport therefore retains their redaction behavior locally with standard
Python libraries. Its isolated fake-runner failure test verifies an actionable
write diagnostic, secret redaction and cleanup without those dependencies.
The previous prepared policy and manifest remain preserved as adjustment evidence.

Finish or stop any existing consumer architecture session before reinstalling its
tools. From a normal user-owned PowerShell terminal, run:

```powershell
& 'C:\Users\tech_\Code\program-kit\artifacts\bootstrap-placement-4af9317f\Prepare-ConsumerRepair.ps1'
```

The script refuses an active workflow, a different failure boundary, changed
candidate hashes or installed tooling that evolved since preparation. It backs
up both installed extensions, reinstalls them through Spec Kit, validates version
coherence and prepares recovery. It starts no agent or workflow. If a guard fails,
inspect the newer state/tooling rather than forcing installation. Review the
generated recovery manifest and its preserved source hashes.

When ready to retry architecture, use the same normal terminal:

```powershell
Set-Location 'C:\Users\tech_\Code\InsurancePolicyEvaluator'
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id 4af9317f
```

The lifecycle establishes workspace-write automatically and checks native access
before history changes. It preserves the successful prefix, archives the failed
attempt, reruns architecture and downstream invalidated stages, and keeps review
verdicts human-owned. The producer should reuse the existing Draft and Proposed
ADRs, reconcile any path/provenance edits, pass structural validation, finish the
narratives and pass full stage validation before review. A validator failure is a
stopped run requiring diagnosis, not permission to invent an approval. Do not
start a new bootstrap, delete partial work or edit saved step results.
