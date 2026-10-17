Implement the approved Program Kit coding-system feature in an isolated feature branch/worktree.

Implementation base: `fc402ef784c025caced1770cd12f64af1a0bdf45` from `origin/main`, fetched on 17 October 2026, plus the documentation handoff containing this prompt. This includes the release/validation redesign and subsequent public-delivery upgrade fixes. Start from that base and preserve its behavior; do not start from the old maintenance branch. If main has advanced, explicitly integrate and inspect those changes before proceeding.

The human approved the complete feature and the later canonical-knowledge, modularity/domain-event, thin-endpoint and browser-quality refinements. They requested that implementation build on the latest main. Approval is already granted; do not request it again. Create or reuse a dedicated isolated feature branch without switching, resetting or cleaning the shared dirty checkout or copying unfinished owner changes.

Work on one F item per human-led session. Investigate actual implementation choices, grill only unresolved decisions, and confirm shared understanding before implementing that item. Follow the plan's session checkpoints and accepted F1 implementation decisions. Each item requires a runnable fixture with inspectable actual output reviewed with the human before its checkpoint closes; define the fixture and its proof limits during the interview. Use both per-item fixtures and final integrated proof through a connected journey plus focused scenarios. Provide a guided review index explaining where to look, what to inspect and what to pay attention to, with actual output and before/after snapshots. Retain review fixtures until the human confirms review is finished, then clean up owned disposable material while preserving scoped proof. Record workflow lessons and adjustments in each session handoff; after the approach has proved useful, create the requested repository development skill from those lessons. Preserve the next-session handoff and do not advance automatically to the next F item.

Read AGENTS.md and these complete current documents:
- docs/reviews/coding-system-plan-and-prompt-2026-10-17.md: F1–F8 and every acceptance row are the feature contract.
- docs/validation.md: Integrity, affected capabilities, prerequisites, budgets and honest coverage gaps.
- docs/releasing.md: exact-source package CI, local validation claims, maintainer disposition and publication authority.
- docs/consumer-engineering.md: ordinary native engineering ownership without duplicate governance lifecycles.

Local continuation: reuse `codex/coding-system-f1` in `artifacts/coding-system-f1`.
F1 is approved, including retirement of C# composition-preset projects; preserve its
checkpoint, validation/cost disclosures and retained review output. F2 was approved
on 18 October 2026 and its commit was explicitly authorized. Its status is recorded in
`docs/reviews/coding-system-f2-checkpoint-2026-10-17.md`. Read that checkpoint and
`docs/coding-context.md` before continuation. The human requested F3 in a fresh session;
that session investigates/interviews F3 against this same worktree, preserves F1/F2
decisions, defines its inspectable fixture and confirms understanding before implementation.
Stop at F3's human review checkpoint; do not automatically advance to F4.
No review cleanup was requested, and the shared dirty checkout remains separate.

Deliver the plan's integrated accepted-context -> applicable composable skills -> safe scaffold/edit -> actual-change reconciliation -> appropriate evaluation route, with private consumer-local patterns and teach/qualify/adopt/improve/retire behavior. Discover rules across references/decisions, prompts/scripts, schemas/build/analyzer settings, templates/examples/tests and exact publisher captures. Extend the existing registry; one authoritative source per rule supplies attributable selection, realization and checks. Resolve generated guidance from canonical sources and remove duplicate/hidden policy only after replacement proof. Preserve independent negative oracles.

Deliver every F5 family, explicitly including modular domain ownership and complete vertical slices, thin transport endpoints delegating business work, justified Foundation domain events with real registered handlers, actual service lifetimes/options/activation/middleware, and coherent rendered browser journeys using applicable maintained capabilities. Preserve the original configuration/construction/SOLID, relational/SQL, async recovery, private diagnostics, journey/resource and native-contract requirements. Use qualified current mechanisms and diagnose actual gaps rather than creating competing frameworks or forcing patterns where they do not apply.

Run Integrity and appropriate affected validation against the implementation base, extending the single maintained capability/check definition when needed. Expensive native/provider/browser/Host scenarios require concrete affected contracts; use explicit --check/--reason where required. Unknown inputs and missing tools are explicit gaps, never a full-inventory fallback. Do not install device toolchains or restore retired Development/Release matrices, campaign-ledger gates, custom release readiness receipts or remote evidence handoffs. Current main's release changes take precedence over historical investigation procedures.

Historical investigation/approval documents are retained in Git at dabe83d85da148ed426ef2fb7dff9088f2f0e5c2 and the original planning checkout. They are optional context, not required active files, current defect proof or implementation prerequisites. Reconcile current native repairs against actual source. Preserve authored code, local patterns, locks, immutable history and private data; keep the stopped trial consumer stopped.

No publication/tagging, paid/provider/worker execution, device installation, consumer reset/deletion/migration or cross-task messaging is authorized. Prepare reviewable changes and report source identities, actual validation, acceptance coverage and remaining gaps. Do not claim feature completion until the plan's acceptance is satisfied.
