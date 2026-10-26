# Optional coding patterns

Current native phases use [focused guidance](coding-context.md) and ordinary plans/tasks. Pattern
inspection and contribution helpers are optional; a consumer needs no toolkit qualification or
evidence-binding ceremony to choose a suitable local implementation. Preserve the actual selected
framework/API, security and behavior contracts. A framework replacement still needs a concrete
capability gap and justification in the normal plan or ADR.

## Inspect declared examples

```text
python .specify/extensions/program-kit-governance/scripts/coding_patterns.py inspect --feature-dir specs/001-notes
python .specify/extensions/program-kit-governance/scripts/phase_obligations.py project --feature-dir specs/001-notes --phase implementation --only implementation-quality
```

Inspection lists applicable declarations and local choices. It does not evaluate an SDK, qualify a
recipe, prove consumer behavior or automatically adopt a pattern. Missing tooling support leaves
manual implementation available. Use real compiler/analyzer, behavioral and integration checks where
needed. [Completion review](coding-evaluation.md) describes the ordinary handoff.

## Deliberate maintainer contributions

For explicitly requested teaching or catalog work, `coding_patterns.py` retains `draft`, `teach`,
`prepare-shared` and evidence-binding helpers. Inspect their current CLI and proof limitations.
The [learning guide](coding-learning.md) describes retained contribution inputs. These helpers do not
restore historical prepare/reconcile/progress protocols as consumer eligibility requirements.

Shared declarations live in the maintained canonical registry; optional private declarations use
`docs/architecture/coding-patterns.json`. Keep source/rule/unit identities unique. Attribution,
semantic identity, version, owner, applicability, selected compatibility, invariants, alternatives,
positive/counterexamples, actual checks and scoped review each have a purpose. An absent dependency
cannot be qualified merely by listing a package. Conflicting choices and stale evidence require real
review when adopting a maintained pattern; they do not grant authority to change a consumer's locks.

Declare only actual proof. A recording fixture is not a live provider, a hash is not an authenticated
reviewer, and a successful check is not human product acceptance. Preserve historical versions,
failures and retired declarations. A consumer cannot rewrite shipped evidence through a local helper.

Shared preparation requires explicit selection of publishable inputs. Inspect the prepared bytes and
normal missing-proof output. No submitted source or declaration is executed by inspection/preparation,
and no private consumer content is automatically copied upstream. Publication, messaging and paid
work retain their own explicit authorization.
