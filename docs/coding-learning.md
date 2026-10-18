# Teaching, applying and sharing a bounded lesson

Use the existing [pattern contract](coding-patterns.md), composer, canonical
sources and native verification owners. Teaching never executes a submission,
registers a pattern automatically or creates a new approval ceremony.

## Prepare one contribution

An explicit teaching request accepts a problem, supplied prose/code/evidence or
known gap. Author one request; references identify existing confined inputs.
Review empty change categories as intentional (a manual recipe needs no renderer).

```json
{
  "schemaVersion": 1,
  "id": "snapshot-query-v1",
  "intent": "new",
  "problem": "Repeated immutable owner queries have no qualified local index recipe.",
  "submission": "docs/patterns/snapshot-query.md",
  "invariants": ["principle.compilation-boundaries"],
  "changes": {
    "guidance": [{"root": "repository", "path": "docs/patterns/snapshot-query.md"}],
    "scaffolds": [],
    "checks": [{"root": "repository", "path": "tests/snapshot_check.py"}],
    "examples": [{"root": "repository", "path": "src/SnapshotQuery.cs"}],
    "acceptedArtifacts": [{"root": "repository", "path": "specs/001-query/plan.md"}]
  }
}
```

```powershell
python .specify/extensions/program-kit-governance/scripts/coding_patterns.py teach `
    --request docs/patterns/teach.json `
    --output artifacts/query-contribution.json
```

The single editable output contains the problem, proposed declaration, change
plan and missing proof. Omit `submission` for a known gap: the request itself is
the draft source until real guidance is authored. An optional `performance`
reference can identify existing observations; presence is not qualification.
Review applicability/exclusions, exact compatibility, examples, checks, canonical
guidance and relevant scaffold changes. Merge explicitly into the existing
local/shared owner, run affected checks, record normal semantic review and bind
actual evidence. Architecture/model proposals go through accepted plans/ADRs and
contract owners. Manual edits retain every mandatory duty.

For `refine` or `replace`, add `basedOn: {"id":"prior-id","version":"1.0.0"}`
and use a new unit identity. Set the exact new version in the proposal; preserve
the old declaration/evidence. Refinement prepares a compatible alternative;
replacement prepares an explicit relationship, not suitability or qualification.
Adopt the exact version in the existing plan choice. For `retire`, keep the
original identity/version/evidence and change status in the existing document.
An old selected retired version blocks without fallback. A new default is
available, not silently adopted; consumer upgrades keep their native owner.

## Qualify a performance proposal

The [finite snapshot-query example](../extensions/program-kit-dotnet/references/examples/snapshot-query/README.md)
demonstrates a package-free .NET extension and measured read-many specialization.
Identify workloads, runtime/configuration, correctness, resources, adverse
tradeoffs and counterexamples. Keep raw samples and limits. A local benchmark
cannot establish a universal rule, and a memory-allocation counter is not process
RSS or retained heap. The preserved scan alternative can cost less for one lookup;
mutating input requires a new snapshot. Database/live-store claims remain outside
this example's qualification.

## Prepare an explicitly selected shared lesson

Author a standalone publishable declaration with `schemaVersion`, `sources`,
`rules` and exactly one `codingUnits` entry, using normal shared extension locators
and the pattern contract. It must be a `draft` with empty `evidence`. Supply reviewed
publishable owner/provenance, guidance, examples, check and review files. Do not
copy a private registry or inspection view. Select every new referenced file;
references do not recursively export dependencies:

```json
{
  "schemaVersion": 1,
  "declaration": "publishable/declaration.json",
  "files": [
    {"source": "publishable/lesson.md", "target": "extensions/program-kit-dotnet/references/examples/my-lesson/README.md"}
  ]
}
```

This illustrates selection syntax; a usable declaration needs its complete
explicit example/check/review file set too.

```powershell
python .specify/extensions/program-kit-governance/scripts/coding_patterns.py prepare-shared `
    --selection publishable/selection.json `
    --output artifacts/shared-lesson
```

Preparation copies only that bounded set into a new local directory and writes
`catalog-additions.json` plus a target/hash contribution manifest and concrete next
actions. Existing output, escapes, missing selected dependencies, execution-history
sources and consumer evidence transfer reject. Review every selected byte for
privacy: this allowlist is not a secret detector or authenticated authorship.
Preparation does not write upstream, submit, message or publish anything.

Review the ordinary source diff and merge additions into `phase-obligations.json`
without shadowing canonical owners. Include maintained scaffold/check/example
changes as needed. Rewritten paths/context require fresh installed positive and
negative execution and shared evidence through the existing `binding`/`current_check`
functions in reviewed source. Normal repository review, CI/package delivery and
explicit consumer version adoption retain their owners. Local evidence cannot
be relabeled as upstream acceptance.

## Inspect actual application and extension proof

`python tests/learning_review_fixture.py --review` retains a new fictional consumer,
one contribution, actually applied later-task C# source/diff, independent compiled
behavioral negatives, bounded raw performance observations, version/retirement
snapshots, exact installed commands, privacy canaries and a separate installed
shared-review copy with fresh source-specific proof. Open its printed unique guide.

The small adapter uses the existing context detector and `codingUnits`; adding
the finite phrase **immutable snapshot query** is not support by registration.
Require owned source/version/context, installed positive and negative execution,
exact compatibility and explicit limits. Unknown applicability, unsupported
executable fields, incompatible/overlapping choices and missing canonical support
diagnose the actual owner. New technologies still need their own maintained
detector/native adapter and proof. Existing selected capabilities retain their
qualified workflows; no dynamic plugin loader or production adopter is required.

Qualification includes detector/composer identities, native evaluated SDK and
current read-only runtime inventory. Changed code, guidance, detector, runtime,
review or checks makes affected proof stale. Earlier versions/failures remain
history. Preparation keeps `applicationObserved: false`; execution is separate.
Authored review is not authenticated identity, observed agent obedience, human
acceptance, F7 general evaluation or F8 packaged adoption.
