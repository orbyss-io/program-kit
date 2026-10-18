# Coding realization and subsequent editing

Use [coding preparation](coding-context.md) and [qualified patterns](coding-patterns.md).
A selected pattern exposes `realization` when its semantic identity is `typed-label`
and its canonical bindings include the maintained typed-operation recipe.
`missingQualifiedInputs` lists the exact source assets/adapters its F3 qualification
must bind. A recipe link alone does not qualify code or establish application.

The first finite adapter creates the shipped single-label example across accepted
Core, runtime implementation, API and PostgreSQL provider owners, with a client
importing the registered native generated types. The endpoint admits/maps HTTP and
passes cancellation; the application capability performs write-then-read. This
promises no atomic write/read snapshot, retry or general transaction contract.
Broader semantic families remain separate qualification work.

Supply one optional JSON convenience input with existing native paths:

```json
{
  "core": "src/Labels.Core/Labels.Core.csproj",
  "runtime": "src/Labels.Runtime/Labels.Runtime.csproj",
  "api": "src/Labels.Http/Labels.Http.csproj",
  "provider": "src/Labels.Store/Labels.Store.csproj",
  "test": "tests/Labels.Tests/Labels.Tests.csproj",
  "frontend": "web/labels",
  "generatedTypes": "tools/openapi/labels/generated/types.ts"
}
```

This is not an approval artifact or application prerequisite. Use normal native
generators/recipes to establish projects, accepted placement and contracts first.
The adapter requires current F2 context, accepted model/contract owners, evaluated
roles and compile references, a native verification owner and the selected frontend's
registered OpenAPI output. The exact selected F3 pattern must cover adapter/source
inputs. Unsupported selected dependencies fail before writing; the typed example
requires the qualified public problem contract introduced in Foundation 0.3.6.

```powershell
python .specify/extensions/program-kit-governance/scripts/coding_scaffold.py preview --feature-dir specs/001-labels --operation update --unit local-label-realization --owners specs/001-labels/label-owners.json
python .specify/extensions/program-kit-governance/scripts/coding_scaffold.py apply --feature-dir specs/001-labels --operation update --unit local-label-realization --owners specs/001-labels/label-owners.json --plan-digest <inspected-digest>
```

Preview is read-only and includes exact source diffs, current/absent byte hashes,
consumer ownership, selected-context identity and remaining integration/evaluation
duties. It can contain private source; keep this deliberate local view private.
Apply recomputes context, qualification, effective settings, imports, contract
inputs, adapter identities and destinations. Changed inputs invalidate the digest.
The existing native transaction owner stages/journals writes and owns rollback and
recovery. Exclusive creation preserves a file authored after the precheck.
Conflicting/interrupted transactions retain their recovery diagnostic. This is
not a global filesystem lock or universal write interceptor.

Creation writes only absent files. Identical output is an idempotent no-op. Any
different existing application file produces a conflict and proposed diff while
preserving it and all other destinations. No replacement/automatic merge is
supported. Created business code belongs to the consumer immediately and never
enters toolkit managed-file ownership. Native managed projections keep their
existing owners; framework updates do not acquire business-code ownership.

Owning features still perform actual service/endpoint registration and shell
selection. Use native options inspection/build/pack, explicit schema deployment,
OpenAPI export/comparison/type generation and strict client checks. No settings
provenance receipt, dependency pin, contract baseline, test success or activation
claim is generated. Test projects remain authored native owners with meaningful
independent tests. `requiredIntegration` and the recipe identify unfinished seams.

Continue manual editing/refactoring through the same selected units and
`phase_obligations.py reconcile`. Missing scaffolding retains a compatible manual
route. Missing mandatory context, checks or invariants remain blockers; a stale
chosen pattern cannot silently become a manual waiver. Compiled/application checks,
semantic review and human product review keep their separate duties.

The canonical [.NET style overlay](../extensions/program-kit-dotnet/references/dotnet-engineering.md#orbyss-style-overlay)
requires prepared argument values, one value per line for lists longer than two,
an aligned closing parenthesis on its own line, and fluent calls below the receiver
with one invocation per line starting with the first. This is mandatory for owned
authored C# and these editable templates, including manual follow-up edits. The F4
fixture regression checks emitted syntax with the installed SDK parser and rejects
independent invalid controls. It is not a shipped consumer analyzer: ordinary
source review still enforces the rule, and green build analyzers do not certify it.

Run `python tests/scaffold_review_fixture.py --review` and open its printed unique
`artifacts/f4-review/<run>/index.md`. It links actual diffs, creations, idempotence,
authored customization/conflicts, independent .NET positives/negatives and blocked
manual completion. Fictional authoring is labeled. The maintained native typed-operation
qualifier supplies separate HTTP/provider/options/generated-client/browser proof.
