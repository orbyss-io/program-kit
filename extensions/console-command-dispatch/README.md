# Generated Console command dispatch review candidate

This directory contains the non-authoritative review candidate for the Program
Kit generated Console command dispatch gap reported by a blocked consumer.

Review in this order:

1. `design-intent.md` — supplied consumer gap, caller-visible outcome,
   constraints, rejected alternatives, and approval boundary.
2. `architecture-design.md` — concise lifecycle, contract, lock/evidence,
   compatibility, shell, and acceptance explanation.
3. `architecture-design.json` — canonical architecture design.
4. `implementation-plan.md` — bounded `PKCCD-W010` through `PKCCD-W040`
   implementation sequence.
5. `implementation-plan.json` — canonical implementation plan and complete
   `PKCCD-R001` through `PKCCD-R012` trace.
6. `validation-report.md` — exact validation scope, commands, outcomes,
   deliberate omissions, and digests.
7. `review-manifest.json` — exact artifact inventory and human approval
   boundary.

The current candidate keeps generated parser and parse-result bytes unchanged,
adds no Program Kit runtime generator dependency, and does not make the base
CShells package optional. A plain Console command may use zero feature
activations and therefore requires no CShells feature package.

Implementation has not started. Creation, validation, commit, or push of this
review set does not approve it. Implementation requires an explicit human
decision over the exact canonical design and canonical plan digests in
`review-manifest.json`.
