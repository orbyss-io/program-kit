---
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user until you reach a shared understanding of the requested scope. Map this as a
**design tree**: every decision branches into the decisions that depend on it. This is Program Kit's
reusable interview method, usable independently for any plan, decision, or idea.

When another Program Kit skill uses this method, keep the interview in the same conversation. That
skill supplies the scope, applicable default policy, artifact contract, and completion boundary;
this skill owns the interview mechanics below. Do not start another agent session to conduct the
interview. Standalone use takes its scope and defaults from the user's request; it does not require
bootstrap artifacts or assume Program Kit technical defaults apply to every topic.

Work the tree in **rounds**. The **frontier** is every in-scope decision requiring a user answer whose
prerequisites are already settled: the questions you can ask now without guessing earlier answers.
Resolve available facts and clearly applicable authorized defaults before forming the frontier.
Ask the whole frontier in one round, grouped by related subject: number each question and give your
recommended answer with its reason and material trade-offs. Keep question IDs stable across rounds.
Then wait for the user's answers before the next round. Do not invent a preference when evidence is
insufficient to recommend an option; explain which missing fact matters.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each answer reshapes the tree. Record the answer, its provenance, rationale, dependencies, and
disposition; recompute the frontier before asking the next round. A question whose answer depends
on another question still open belongs to a later round. Partial answers leave unanswered questions
open; continue independent branches without repeating settled questions. "Accept all recommendations"
settles only the recommendations actually presented in the current round, subject to any explicit
exceptions or corrections. It does not settle future questions or confirm an unseen final synthesis.
Acceptance of a conditional recommendation does not establish its premise. Record the accepted
policy separately from the unknown fact (for example, reuse an existing provider *if one exists*).
Resolve the condition through evidence or a focused question only when it affects the requested
outcome; otherwise retain it as explicitly assigned. Do not convert a planning estimate or a
conditional fallback into an observed property of the user's organization.

Challenge contradictions and weak assumptions with evidence. When the user changes a decision,
invalidate only conclusions that depend on it, preserve unaffected answers, and reopen the affected
branches. Maintain a compact decision record so the conversation can resume without reconstructing
every round. Use the calling skill's existing artifact for this record when it has one.

Finding accessible facts is your job. Inspect the relevant evidence within the task's discovery
boundary; don't ask the user for information you can look up. For an independent substantial
investigation, dispatch a sub-agent when available and permitted; small lookups need no delegation.
A pending investigation is an unsettled prerequisite, so only its dependent questions wait. Product
intent and preferences remain the user's decisions. Label unavailable facts as unknown and record
what evidence or owner can resolve them instead of guessing.

An empty frontier is necessary but not sufficient for completion: check every relevant branch for
unanswered questions, pending evidence, and unresolved dependencies. Every branch must be answered,
covered by a disclosed applicable default, excluded, or explicitly assigned/deferred with an owner
or next action and a trigger. A decision that blocks the requested outcome cannot be hidden by
assigning it to later work. Exhaust the agreed scope, not every possible future decision.

Prepare a concise synthesis for one shared-understanding review, including applied defaults,
proposals, material consequences, and open/deferred items. Preparing and validating review drafts
is part of the interview and needs no separate confirmation round. Do not act on it until the user
confirms the synthesis: this boundary applies to executing the proposed plan or marking its result
confirmed, not to producing those review drafts. Use the calling skill's final review as this same
gate; do not add another grilling approval. Existing explicit approval of the exact synthesis counts;
silence, partial answers, and approval of a question round do not.
