---
description: Find relevant architecture and engineering references for the current native phase.
scripts:
  py: scripts/phase_obligations.py
---

Use the native Spec Kit feature directory and the existing spec/plan/tasks. Before planning run
`{SCRIPT} project --feature-dir <feature> --phase planning`; before tasks use `--phase tasks`.
The result is a compact attributable index. Use `--only <id>` for a relevant unresolved mechanism
and `--page <n>` to continue long detail. Read only the sources needed for the current decision.
Lexical selection is a starting point: inspect actual source and correct missing or irrelevant
context. An index does not perform research, judge a design, invoke coding methods or run checks.
If a relevant read is truncated, recover the missing guidance through bounded source sections or
the focused lookup and its continuation before claiming that review. A command naming a file does
not establish that its contents were returned or applied; avoid combining large source dumps.

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

For consequential discoveries use the shared [engineering feedback method](references/engineering-feedback.md).
Report native Analyze findings first, then make any authorized correction as a separate explicit
step through the owning documents/source. Preserve unrelated decisions and completed task IDs.

For .NET host/exporter choices, apply `principle.dotnet-host-default` in
references/tool-selection.md. Review a custom-host proposal against actual human opt-out,
keep unresolved choices visible, and resolve the effective profile before reading versioned
package knowledge. A proposal, helper pass or profile listing supplies no human acceptance.
