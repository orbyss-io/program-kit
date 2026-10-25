---
description: Find relevant architecture and engineering references for the current native phase.
scripts:
  py: scripts/phase_obligations.py
---

Use the native Spec Kit feature directory and the existing spec/plan/tasks. Before planning run
`{SCRIPT} project --feature-dir <feature> --phase planning`; before tasks use `--phase tasks`.
The result is a compact attributable index. Use `--only <id>` for a relevant unresolved mechanism
and `--page <n>` to continue long detail. Read only the sources needed for the current decision.

Use the project's constitution, ADRs, plan and local guidance for its choices and agreed reviews.
Support a suitable custom stack or manual alternative. Curated patterns are useful defaults;
consumer choice does not need qualification in a toolkit registry. Actual selected library, compiler,
SDK, security and product contracts remain constraints. Explain unknown facts and investigate them.

Record consequential decisions, tests, exact prerequisites and agreed human review points directly
in plan.md/tasks.md. Preserve existing IDs, checked boxes, failures and local edits on resume. Save
useful task groups as they are ready. No hidden task checkpoint, approval receipt, bootstrap history
or new phase ledger is needed. Drafting does not run application checks or start services.

Keep native task generation and configured hooks. After the complete task plan, use the normal
read-only analysis. The guidance helper is read-only and supplies no implementation or acceptance
claim; tools selected for an engineering action enforce only the inputs they actually use.
