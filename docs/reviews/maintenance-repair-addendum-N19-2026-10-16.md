# Proposed N19: focused review projection rejects native verification globals

Prepared 16 October 2026 for the consolidated collection queue. This is an independently reproduced adapter interoperability mismatch. It is related to N3's scoped-review capability, but distinct: N3 concerns materiality of unrelated changes, while N19 concerns rejection of the native manifest's supported fields before a focused projection can be used. No production or consumer code, historical plan/audit or active implementation ledger was changed.

## Evidence and root cause

The consumer chat reports that a supported focused verification projection rejects its current native manifest's runner/provider-isolation declarations. Its whole-manifest canonical-JSON projection succeeds without changing verification policy or bypassing freshness. At collection time this arrived as a chat diagnostic; no new numbered report section beyond D53 had yet been found.

Current `extensions/program-kit-governance/scripts/review_material.py:basis`, in the `kind == 'verification'` branch, permits only schemaVersion, testGroups, runnerReuse, testOwnershipReplacements and owner at the manifest top level. A native verification manifest with runner or providerIsolation is rejected as unknown verification version/fields. The native `repository_verification` configuration reader preserves these declarations; runner selection explicitly consumes runner. The inspected real consumer manifest uses schemaVersion 1, runner=adapter, providerIsolation.required=true and declared test groups.

An independent synthetic API probe reproduced all three observations:

1. Native configuration reader preserves the manifest, including runner and providerIsolation.
2. The focused verification projection rejects that same manifest with the stated error.
3. The already supported canonical-JSON kind binds the complete manifest successfully.

The probe record is `artifacts/maintenance-research-2026-10-16/projection-probe/result.json`, containing the minimal manifest/scope, observed outcomes and exact inspected source hashes. It created only disposable owned synthetic files and that evidence record. It did not execute consumer tests, a coding agent, native restore/build or full runtime/schema qualification. Native reader acceptance alone does not validate every arbitrary value of a global field; the observed mismatch must be resolved against all authoritative native consumers/validators, not their most permissive reader.

The immediate cause is a separately maintained restrictive field set in the governance projection drifting from the native manifest it is intended to project. Existing focused projection tests need actual emitted/current native manifests, not only minimal fixtures without current globals.

## Assessing the continuation

Whole-manifest canonical JSON is conservative: it binds all globals and groups, so it may cause unrelated later changes to reopen review but cannot silently omit them. It is a valid supported representation for a new/reconciled scope where the native transition and actual human authority permit it. Do not replace a historical review basis in place, claim an earlier reviewer approved a different basis or infer fresh acceptance from the successful hash operation.

Repairing the focused kind must not omit runner/isolation/global policy to avoid the rejection. It must retain every global declaration with its relevant semantics while filtering only the intended selected-project group scope. Unknown or malformed fields must fail actionably rather than be ignored. Do not use a broad **accept arbitrary keys** change as a substitute for authoritative manifest validation.

## Planned work and required closure

**Owners:** Program Kit governance material projections, native verification contract and their installed integration tests; coordinate with existing N3 work. Keep N19's explicit regression and disposition even if repaired in the same commit as N3.

- Establish the authoritative supported verification and setup-manifest versions/fields across generator, native readers/validators and projection. Reuse a versioned shared contract where practical, without creating a dependency on consumer-specific global settings. Include optional/default forms and required owner boundaries.
- Update focused admission to support the current native contract while retaining all global policy in the resulting digest. Validate group schema, selection coverage, ownership/replacements and ambiguity consistently. Preserve full selected groups and any dependencies needed for their actual meaning; do not silently truncate a mixed selected group.
- Retain conservative rejection and an actionable full-JSON fallback for unsupported projection versions/contracts. Whole-JSON support is not a verification-policy waiver.
- Bind the projection implementation/contract version and resulting scope in current evidence. Changes to projection definitions require legitimate reconciliation/fresh engineering; preserve old scope/decision records unchanged and do not manufacture approval.
- Add an installed integration case using an actual current generated native manifest with runner/provider-isolation and applicable setup/ownership fields. Include the exact previously rejected field set as a regression, rather than relaxing a mocked function.
- Prove changing runner or isolation/global policy changes the material digest and makes prior material evidence stale. An unrelated nonselected group may remain nonmaterial only under the declared projection. Selected-group additions/edits, unknown globals, duplicate JSON keys, malformed values, missing project coverage and tampered projection definitions fail or invalidate as required.
- Compare the conservative JSON binding and focused binding deliberately: the former remains sensitive to the whole manifest, and the latter preserves every global plus its complete selected groups. Neither binding alone claims tests ran or a human review occurred.

**Closure:** passing central native/projection interoperability and sensitivity/negative tests, current installed command behavior and an accurate migration/authority disposition. No duplicate consumer framework tests, historical receipt edits, policy relaxation or paid execution.

## Collection disposition

N19 is queued for consolidated review, not forwarded individually. The latest inspected active implementation ledger remains at 47 findings with N13–N15 adopted. N16–N19 are four proposed additions, yielding a combined distinct inventory of 51 if all are adopted. Reconcile the actual ledger again before final delivery; these counts describe findings/opportunities with explicit attribution, not 51 confirmed product-code defects.
