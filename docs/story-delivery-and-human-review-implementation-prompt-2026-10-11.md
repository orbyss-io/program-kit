# Fresh session prompt for story delivery and human review

Use this prompt in a fresh Program Kit session after the current official release has succeeded. The [accepted plan](story-delivery-and-human-review-plan-2026-10-11.md) contains the complete requirements. This prompt starts no session and grants no publication, live-worker or real-consumer reset authority by itself.

```text
Implement the accepted story delivery and human review plan for Program Kit.

Read these files in full:
C:\Users\tech_\Code\program-kit\AGENTS.md
C:\Users\tech_\Code\program-kit\docs\story-delivery-and-human-review-plan-2026-10-11.md

The design interview is complete and the user has accepted the decisions. Resolve routine implementation choices yourself. Ask only about new consequential conflicts that the plan cannot resolve.

Start by verifying that the predecessor's complete official tagged Release succeeded and its published assets are available. Reinspect the current repository and instructions; start from the published committed baseline. Do not work in the releasing agent's frozen checkout or modify its release candidate. Use a dedicated implementation branch and suitable isolated worktree when needed. Preserve unrelated changes. These two handoff documents may be uncommitted in the primary checkout; read them there and copy only them into your implementation checkout as needed.

Implement the plan with these final policy choices:
- Human review is required per completed user story, not per internal operation. Earlier checkpoints require explicit agreement. Stories must be small enough to reach a useful integrated journey promptly.
- Materialize established scaffolds/templates coherently first, run maintained checks, then add missing consumer-specific tests. Choose test-first for critical/uncertain behavior and reproducible bugs; allow other appropriate sequences for straightforward changes. Verification remains required.
- Present runnable stories after exercising them and passing relevant technical checks. Default to pausing before further product work at a required human checkpoint; acceptance or explicit bounded deferral permits the corresponding scope.
- Persist separate engineering/human dispositions, exact reviewed outcome/basis, decision source, review-role identity, scope and freshness. Required deferred reviews remain due before feature acceptance. Material changes reopen affected acceptance, while unrelated commits do not invalidate everything.
- Default the feature owner/reviewer to the requesting human. Support explicit delegation and optional confirmed GitHub account bindings. Read explicitly supplied authenticated decision references; add no automatic posting or monitoring. Reviewer and owner powers remain distinct.
- Use advisory drift defaults of 60 active minutes per operation and two active hours per story. Include preparation, builds, tests and repairs; exclude human waiting and preserve accounting on resume. Warn and reassess, but never block implementation solely because a time threshold was exceeded.
- Existing consumers adopt by abandoning the affected partial feature, amending/ratifying the constitution, and rerunning all Spec Kit phases from fresh specification. Reuse unchanged confirmed bootstrap/intake intent and accepted project context. No mid-specification or mid-implementation continuation is supported for this improvement.

Qualify fresh specifications and the maintained reset contract with one concise installed fixture, reusing existing installed-workflow setup. Do not add a historical feature-migration matrix, another package installation loop, real consumer/data migration, live coding-agent trial or service cohort. Keep existing toolkit installation/recovery/publication coverage.

Inspect canonical templates, command overlays, projected guidance, state helpers and installed output together. Enforce review/progression/resume/closure contracts through existing validators, including formal handoff and the no-hook path. Keep engineering commands independently runnable. Use one compact canonical feature state and existing logs, without new approval dossiers or a framework.

Use targeted checks during edits and bounded Development for integration. Keep added test cost small; expand only for changed responsibilities or real failures. Preserve mandatory dependency maintenance, local Release, CI and tagged publication gates. Follow the Windows Firefox and local Release instructions. No real consumer should be deleted/reset and no release should be published under this implementation prompt alone.

Continue through implementation, review, repairs and development qualification. Maintain one compact checklist linked to the plan. Finish with requirement-by-requirement results, actual tests and artifact references, installed-policy/reset verification, concise adoption instructions, and any outstanding publication gates. Do not claim the change fixes agent delivery time based only on deterministic fixtures.
```
