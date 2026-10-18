# Versioned coding pattern inputs

Patterns enrich the existing `codingUnits` in the responsibility/source registry.
`prepare`, `reconcile`, progress and completion use the same composer. F2 units
without pattern metadata retain their existing behavior and proof scope. F3 does
not retroactively qualify those units or supply F5's semantic seed families.

Shared declarations live in `phase-obligations.json`. Private consumer declarations
live in one authored `docs/architecture/coding-patterns.json` with `schemaVersion: 1`,
`sources`, `rules` and `codingUnits`. The local collections extend that registry;
they cannot shadow a shared source, rule or unit identity. Repository-owned rules
resolve through the same confined canonical-source resolver. Rule text belongs in
that source, not in another policy summary inside pattern metadata.

## Preparing a submission

From the consumer, supply an existing prose or code file:

```powershell
python .specify/extensions/program-kit-governance/scripts/coding_patterns.py draft --submission docs/patterns/owner-query.md --id owner-query --invariant principle.compilation-boundaries --output artifacts/owner-query-draft.json
```

The helper creates one editable draft, references the submission and lists missing
proof. It does not overwrite an existing output, register the draft, infer semantics
from prose, qualify an API or execute supplied code. The normal coding agent/human
can assist with the fields; unsupported semantic detection remains explicit. Merge
reviewed sources/rules/units into the single local document. Keep a new canonical
rule `recommended` unless its actual owner establishes a stronger obligation.

`coding_patterns.py:validate` owns the versioned executable contract. In addition
to F2's applicability, context slots and manual-edit/bound-recipe route, a unit's
`pattern` contains:

| Field | Meaning |
| --- | --- |
| `schemaVersion`, `semanticId`, `version` | Contract version 1, semantic choice family and exact three-part pattern version |
| `owner`, `provenance`, `limits` | Accountable source/reviewer and bounded claims |
| `status` | `draft`, `active` or `retired`; retirement preserves prior declarations/evidence |
| `invariantRuleIds` | Canonical invariant references, resolved alongside the unit's rules |
| `compatibility` | Required/excluded profiles, admitted evaluated frameworks and exact observed package versions |
| `alternatives`, `replaces` | Same-family compatible relationships; replacement requires an explicit choice |
| `inputs`, `examples.positive`, `examples.negative` | Exact owned code/evidence references; no executable command fields |
| `checks` | Existing named `toolkit` check IDs or `native` project/arguments/configuration bindings |
| `review` | Ordinary authored semantic-review source, optionally a focused source selector |
| `evidence` | Append-only content bindings to actual checks, review inputs and declared proof limits |

References contain `root` (`repository` or `extensions`), a confined relative `path`
and optionally an existing canonical-source `selector`. Declare actual transitive
inputs in the normal verification owner. An absent dependency cannot be qualified
by merely listing a package. `frameworks`/`packages` compare evaluated .NET facts;
other language adapters remain unsupported rather than inferred from these fields.
No range algebra, numeric ranking or universal prose interpretation is supplied.

## Choosing, inspecting and qualifying

A single applicable qualified pattern can join a task automatically. Replacing a
shared recommendation or choosing among compatible alternatives requires an exact
scoped choice in the existing plan:

```markdown
<!-- program-kit:pattern-choices -->
{"owner-query":{"id":"private-owner-query","version":"1.0.0","reason":"Reviewed specialization for this owner's query contract."}}
<!-- /program-kit:pattern-choices -->
```

The JSON keys are semantic identities. The unit's existing `when` predicates still
select applicability; a feature-wide choice does not pull an unrelated operation
into scope. Unknown, incompatible, retired or wrong-version choices diagnose the
normal owner. Compatible overlapping declarations without a choice are ambiguous;
qualification is not a substitute for contextual suitability. An unqualified draft
is visible but inactive. A previously bound automatic pattern whose proof is stale,
or an explicitly chosen pattern without current proof, blocks affected work. There
is no silent fallback. Other operation/feature scopes remain independent.

No relationship removes ordinary F2 obligations. Alternatives cannot omit declared
invariants or mandatory/conditional canonical duties of their counterpart. Accepted
model, architecture, native profile and contract changes still return to their owners.

```powershell
python .specify/extensions/program-kit-governance/scripts/phase_obligations.py prepare --feature-dir specs/001-notes --operation list --format json
python .specify/extensions/program-kit-governance/scripts/coding_patterns.py inspect --feature-dir specs/001-notes --operation list
```

The output separates precedence, suitability and qualification. It contains local
canonical source text for the local coding task; it is not a public export. Public
failure diagnostics contain bounded identities and repair routes rather than source,
review prose or raw native failures. Unrelated private files are never exported.

Run checks explicitly through the existing verification owner. Pattern preparation,
inspection and evidence binding never execute check declarations or submitted code.
Native evidence uses `repository_verification.plan` to verify current inputs,
toolchain/environment, configuration/arguments, retained reports and unresolved
failures. Named toolkit checks use their existing exact input/runner fingerprints,
actual exit, retained streams and unresolved-failure history. Those checks remain
labeled toolkit evidence; they do not become native application tests.

After ordinary authored semantic review and real successful checks:

```powershell
python .specify/extensions/program-kit-governance/scripts/coding_patterns.py bind-evidence --feature-dir specs/001-notes --operation list --id private-owner-query
```

This appends a binding to the local pattern. It neither creates a separate approval
receipt nor infers the reviewer's authority or human product acceptance. Shared
source maintainers record bindings with the same maintained `binding`/`current_check`
functions in ordinary reviewed source changes; a consumer cannot rewrite installed
shared evidence through this helper. Shared promotion is a separate explicitly
selected contribution, never automatic copying of local declarations or private code.

Bindings cover pattern routing/compatibility, resolved canonical fingerprints,
declared code/examples/review, observed profile/framework/package context and the
composition/resolution adapters. Actual check records and hashes must still match.
Changed inputs require affected checks/review and a new appended binding. Optional
`--expires-at <timezone-aware-ISO-instant>` adds an expiry; there is no arbitrary
universal age limit. Prior records remain stale history. Keep exact prior versions
when improving/replacing a declaration and retain a retired declaration when removing
its active route; the toolkit never relabels old evidence as current success.

Hashes detect declared changes, not maliciously forged local evidence, undeclared
dependencies or mutable external state. Review source presence is attributable
authored evidence, not authenticated reviewer identity or automatic semantic analysis.
Qualification is always bounded by its checks/review and `limits`. No compiler,
database, browser, agent application or performance claim follows from routing.

## Inspectable contributor proof

Run `python tests/pattern_review_fixture.py --review` in the feature worktree. Open
the printed unique `artifacts/f3-review/<run>/index.md`. It links real installed-layout
command output, a fixed independent owner-filter oracle, shared/local selection,
later-task use, unrelated exclusion, stale/incompatible/retired inputs and unchanged
mandatory duties. Fictional authoring/reviews and the tiny Python example are labeled.
No PostgreSQL/HTTP/.NET implementation or full F6 learning claim is inferred. Retain
all review material until the human finishes inspection.
