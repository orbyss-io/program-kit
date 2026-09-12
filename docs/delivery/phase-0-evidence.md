# Phase 0 results and capability evidence

Phase 0 completed on 2026-09-12. The common contract, source-hashed provider probes, deterministic failure fixtures and Development validation support proceeding to the Phase 1 interview. This is evidence for coordination primitives and reference behavior, not a claim that consumer activation or complete delivery adapters already ship.

Review the [adapter contract](adapter-conformance.md), [JSON Schema](contracts.schema.json), [record examples](examples.json) and [machine-readable evidence](phase-0-results.json). Original per-run evidence, including failed experiments, remains under `artifacts/delivery-phase0/runs/`; the public summary preserves its hashes and outcomes without credentials.

## Tested resources and boundaries

The user approved these private disposable resources, which remain available for inspection:

- Azure DevOps Services: [ProgramKit.Delivery.Phase0](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase0), system Agile process, `delivery-coordination` repository and synthetic work items.
- GitHub.com: [orbyss-io/program-kit-delivery-phase0](https://github.com/orbyss-io/program-kit-delivery-phase0) and [Program Kit Delivery Phase 0](https://github.com/orgs/orbyss-io/projects/1).

All mutations were confined to these resources. No shared process or organization issue-type configuration was changed. One synthetic deletion item per applicable test was removed; the project/repository scopes and remaining evidence were retained. Final ledger inspection found zero active probe claims and zero unresolved operation records on either provider.

Interactive access used the existing Azure CLI and GitHub CLI facilities. GitHub required an additional `project` scope, granted through the user's device authorization. Windows trusted roots were used with TLS verification enabled. No credential value is included in profiles, source or evidence. These were ordinary API/Python concurrency tests, not paid coding-agent runs.

## Capability matrix

| Capability | Azure DevOps Services | GitHub.com | Contract consequence |
|---|---|---|---|
| Conditional operational commit | Three final independent-process races: one accepted update and one rejection each; stale error was HTTP 409 `GitReferenceStaleException`. | Three final independent-process races: one accepted update and one rejection each. Concurrent losers returned GraphQL `FORBIDDEN`; a separate known-stale request returned `STALE_DATA`. | Entitlement follows a confirmed conditional commit. Generic `FORBIDDEN` is not silently classified as a retryable stale conflict. |
| Claim takeover | New generation committed; each obsolete generation failed its checkpoint. | Same outcome. | Manual transfer fences participating old sessions at checkpoints; no timer-based reassignment. |
| Work-item creation recovery | Matching item recovered after injected loss of identity persistence. | Same; new items were temporarily absent from listings and remained unknown until visible. | No second create on an empty result. Re-observe and verify correlation/destination/payload. |
| Concurrent shared-description editing | Stale `test /rev` update rejected and newer description retained. | Adapter refused unprotected shared-body replacement; proposal comment retained alongside the newer body. | Adapter automation differs; human text preservation does not. |
| Native hierarchy | Feature/User Story relation created and read back. | Sub-issue relation created and read back. | Native relationship primitives are available; complete four-tier planning follows later. |
| Dependencies | Predecessor/successor relation created and observed. | Blocked-by relation created and observed. | Native link alone does not establish satisfaction evidence or scoped activity gates. |
| Visible metadata | Tags written with dependency probe. Agile User Story field/state discovery recorded. | Repository label written; existing organization types were Task, Bug and Feature. | Epic/Requirement GitHub mappings need explicit fallback/setup decisions in Phase 5. |
| Project fields | Not applicable to the GitHub Project identity distinction. | Private Project, text field and membership created; value and distinct project/item/issue IDs read back. | Field discovery works. The write is not a proven conditional update and does not authorize overwriting concurrent edits. |
| Comments/history | Comment created; bounded update-history page observed. Comments API required `7.1-preview.4`. | Proposal comment retained; `userContentEdits` and comment pagination read successfully. | Coverage and continuity must be tracked; one page is not complete history. |
| Deletion | Synthetic deletion followed by failed item read. | Synthetic deletion followed by failed issue read. | 404 alone remains ambiguous unless deletion provenance is known. |
| Access loss, rate limiting, outage, history gaps | Deterministic failure fixtures. | Deterministic failure fixtures. | Unknown/inaccessible cannot establish readiness; no real account permission revocation or provider outage was induced. |
| CI workload identity, protected-branch provisioning, server editions | Not exercised. | Not exercised. | Remain unverified implementation requirements, not implied support. |

Each race used two separate Python processes, both starting from the same recorded head and a barrier before mutation. Across the six final races there were six accepted claims and six rejected competitors, with no duplicate entitlement. The final provider runs record hashes of the probe source files. These bounded results support the documented expected-head primitives; they are not a proof against arbitrary external writers or a guarantee of uninterrupted service.

## Findings that changed the prototype

1. **Azure Comments API version:** an initial comment call using stable `7.1` was rejected with `VssInvalidPreviewVersionException`. The endpoint requires `7.1-preview.4`; affected work-item checks and the final Azure run passed after correction. [Microsoft API reference](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/comments/add-work-item-comment?view=azure-devops-rest-7.1).
2. **Delayed GitHub listings:** an initial assertion incorrectly expected immediate discovery after creation. The failed evidence was preserved, the existing item was recovered without recreation, and the prototype now records unknown outcomes while safely re-observing. Final tests observed this path successfully.
3. **Lagging GitHub reference reads:** a later operation encountered a stale head after an acknowledged write. Reading through GraphQL alone did not remove the problem. The prototype now compares ancestry against its last acknowledged head, retains that minimum when a read is behind, and blocks diverged history. It still uses conditional writes, so unseen newer changes cause rejection. Deterministic regression checks and the final live run passed.
4. **Incomplete history is a real limitation:** GitHub exposes content edits, but currently retains only the original plus the most recent 99 changes. A fully paginated response therefore does not prove unlimited history or continuity with an old checkpoint. Persist observations and require review when continuity cannot be established. [GitHub history limit](https://github.blog/changelog/2026-07-02-issue-fields-are-now-generally-available/).

GitHub organization issue fields are also now generally available, distinct from Project-local fields. The approved Project-based proof remains valid; Phase 5 should evaluate native issue fields through capability discovery and avoid competing authoritative copies. No organization field configuration was changed by Phase 0. [GitHub issue-field announcement](https://github.blog/changelog/2026-07-02-issue-fields-are-now-generally-available/).

## Validation and remaining implementation

The 21 offline tests pass. They cover every schema/example variant, disabled mode, version and profile mismatch, approval fingerprints, incomplete observations, claim/resource conflicts, takeover/release fencing, conservative recovery, revision-bound evidence, path/contract overlap, empty scope and lagging/diverged coordinator history. Development and CI/Release deterministic wiring include this validator; the live scripts are never invoked by those suites.

The bounded `scripts/Test-ProgramKit.ps1` Development suite passed. Its offline bundle check reported normal catalog-verification notices and concluded that the bundle is well formed and valid. The Development log is preserved at `artifacts/delivery-phase0/development.log`; targeted checks also passed after the final empty-scope and workflow-wiring refinements. No browser acceptance was required by these changes.

Phase 1 must implement the optional extension, profile activation, templates and the core authority seam. Later phases must implement actual authorization, protection-policy discovery, reconciliation history continuity, full mutation recovery, claims/checkpoints in consumer execution, dependency/evidence gates, and both provider journeys. Preserve the tested limits: no native issue lock assumption, no atomic multi-item promise, no automatic replay of ambiguous creation, no silent business or architecture revision, and no permission inferred from an actor's ability to write.
