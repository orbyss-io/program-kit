# Feature intake

Use the feature request, current spec, product intent, constitution, relevant ADRs and architecture.
Reuse settled answers. Grill only consequential unresolved choices and explain actual alternatives.
Keep a useful actor outcome with success/failure examples, non-goals, dependencies and test intent.
Confirm substantive choices with the human and record that answer in the spec or readable note.

Ordinary native specifications require no roadmap ID, intake brief, status receipt or SHA256.
Use native specify/clarify/plan/tasks/implement with useful guidance. Preserve agreed story review
points in normal plan/tasks/checklist notes; successful generation never supplies human acceptance.

Optional structured intake remains available:

```text
python specification_intake.py --repository . begin --feature request-registration --request "Record a request"
python specification_intake.py --repository . context --feature request-registration
python specification_intake.py --repository . review --feature request-registration
python specification_intake.py --repository . check --feature request-registration
python specification_intake.py --repository . check-spec --spec specs/001-registration/spec.md
```

begin preserves existing answers in docs/architecture/feature-intake/<feature>/brief.json.
The selected structured helper validates its own meaningful fields and decision dependencies;
an empty/incoherent selected brief still fails. review renders the content without writing a
review packet or basis receipt. check inspects content and supplies no confirmation authority.
Optional --entry names an existing roadmap identity; it is not required to start a feature.

A spec may optionally link **Intake brief** to a real repository-contained JSON/Markdown document,
or record **Architecture scope** as comma-separated canonical IDs when scoped knowledge is useful.
Supplied links/scopes must be real. A normal titled spec without those annotations works directly.
Human confirmation remains a real conversational responsibility, not a CLI receipt.

Existing product open questions are context, not a mandatory all-items applicability matrix.
Carry questions relevant to the selected feature with owners and actual triggers in its normal
spec/plan. Unrelated future questions stay deferred. No English-trigger inference or bootstrap
prerequisite ledger controls phase eligibility. Actual runtime/provider/engineering evidence
remains distinct from a product answer.
