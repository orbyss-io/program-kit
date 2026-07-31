# develop-software

## Identity and trigger

`develop-software` owns development-flow routing for a human-started software
request. Use it when a human asks to develop software but has not selected the
design, approved-plan implementation, or bounded maintenance flow, or asks
which backed development flow should handle the work.

## Purpose

Classify the explicit request together with accepted repository artifacts and a
fresh capability-readiness snapshot. Produce exactly one routing outcome:
`routed`, `human-decision-required`, or `flow-unavailable`. A routed outcome
names exactly one next capability and never grants authority.

## Non-goals

- Do not design or implement the requested software.
- Do not approve a design, plan, release, deployment, or destructive action.
- Do not treat routing as authority to start another flow.
- Do not route release qualification, promotion, or publication into a
  development capability.
- Do not create hooks, watchers, autonomous loops, MCP bindings, tool bindings,
  runtime services, or provider integrations.

## Inputs and outputs

Inputs:

- The human's explicit request or intent.
- The current repository-owned source truth and accepted artifact state.
- The exact active capability catalog: CLI-verified in a consumer workspace,
  or the canonical index plus fresh provider-local source projections in the
  Program Kit source authoring workspace.
- Any named design, plan, approval, or supersession evidence needed to classify
  the request.
- Accepted architecture and current source truth needed to distinguish a
  bounded compatible change from material new intent.

Outputs:

- One explicit routing outcome with a reason.
- Exactly one next capability reference when the outcome is `routed`.
- A digest-bound development receipt when the backing Program Kit operation is
  available and the human requests a durable receipt.
- A concise refusal or decision request when routing cannot proceed safely.

## Preconditions

- A human has started or requested the work.
- The repository and intended scope are explicit.
- In a consumer workspace, the installed CLI reports the active wrapper and
  complete closure as ready and any named next capability passes its exact
  `capabilities preflight`.
- In the Program Kit source authoring workspace, the authoring marker,
  canonical index, and finite provider-local registration agree, and the named
  next skill in the active provider's registered root contains its complete
  current canonical definition.

## Allowed actions

- Read repository guidance, the active capability catalog, and explicitly
  relevant design, plan, approval, and receipt artifacts.
- Validate supplied artifacts with deterministic Program Kit operations.
- Calculate exact file digests needed by a routing result or receipt.
- Recommend one available next capability or stop with one of the two
  zero-capability outcomes.

## Prohibited actions

- Do not infer approval, authority, identity, time, or evidence.
- Do not route to an unavailable, missing, or unregistered capability.
- Do not edit source, design, plan, capability, index, or runtime files.
- Do not inspect sibling repositories or unrelated history.
- Do not access secrets or the network unless the human separately authorizes
  an in-scope read.
- Do not run destructive commands.

## Stop conditions

Stop with `human-decision-required` when intent, scope, repository, accepted
artifact state, semantic mapping, or the choice among maintenance, design, and
approved-plan implementation is ambiguous. Stop with `flow-unavailable` when
the requested flow is absent or unavailable, including release, qualification,
or promotion flows. Stop without routing when a named approval is missing,
changed, rejected, conditional, or superseded.

## Source of truth and freshness

The current human request wins over remembered context. Repository-owned
artifacts are authoritative only at their exact current bytes. Capability
availability, active-provider registration, and complete-closure freshness are
separate facts. In a consumer workspace they come only from `program-kit
capabilities catalog --workspace-root . --format json`. In the Program Kit
source authoring workspace they come from the canonical index, authoring
marker, and finite provider-local source-projection inventory. Provider
adapters and source projections are registration mechanics, not procedure or
availability sources.

## Procedure

1. Confirm the human-started request, repository, and requested outcome.
2. Read applicable `AGENTS.md` guidance. In a consumer workspace, run
   `program-kit capabilities catalog --workspace-root . --format json`. In the
   Program Kit source authoring workspace, inspect the canonical index,
   authoring marker, and active provider's local projection inventory directly;
   do not invoke consumer capability delivery.
3. Identify explicit accepted design, plan, and approval artifacts without
   searching unrelated history.
4. Validate any artifact needed to distinguish a bounded compatible change,
   new/material intent, and an exactly approved implementation plan.
5. Classify:
   - one small architecture-compatible change -> `maintain-software`;
   - new or materially changed architecture, mechanism, schema kind, security
     boundary, package family, compatibility, deployment, or runtime topology
     -> `design-software`;
   - exact valid approved plan -> `implement-software-plan`;
   - unclear semantics, mapping, scope, or missing decision ->
     `human-decision-required`;
   - unavailable flow -> `flow-unavailable`.
6. In a consumer workspace, run `program-kit capabilities preflight
   <capability-id> --workspace-root . --format json`; record exactly one next
   capability only when it is `ready`. In the Program Kit source authoring
   workspace, verify that the selected provider-local projection contains the
   exact canonical definition and record it only when that finite
   registration is intact.
7. If a durable result is requested, bind the request/artifact and index bytes,
   supplied principal/time/evidence, and selected outcome through the backed
   Program Kit receipt contracts.
8. Report the outcome and stop. Continue into the selected flow only after the
   human explicitly requests or confirms that continuation.

Judgment occurs in steps 3-6. Deterministic validation and hashing support the
decision but do not make it or grant authority.

## Verification and failure reporting

Verify that the outcome is one of the three allowed values, zero-capability
outcomes contain no next capability, a routed outcome contains exactly one
available capability, and any receipt binds exact current digests. Report
missing artifacts, unavailable flows, validation failures, and freshness
failures explicitly; never fall back to a guessed route.

## Authority and safety boundaries

The human retains all authority. Routing conveys no approval and no permission
to modify files, use secrets, access the network, or take destructive actions.
Filesystem reads stay inside the named repository. Any later mutation follows
the selected capability's narrower authority and safety rules.

## Compatibility and versioning

Preserve this stable capability ID while routing semantics remain compatible.
Changes to outcomes, authority boundaries, required inputs, or receipt meaning
require an explicit compatibility review and updated capability digest.
Renames, splits, supersession, or retirement require human authority, an index
update, wrapper migration, and no stale registration.

## Program Kit knowledge and failure resolution

In a consumer workspace, use `program-kit commands describe <command-key>
--format text` before invoking an unfamiliar backed operation, and retrieve
diagnostics, schemas, and the `software-change-troubleshooting` resource
through the installed CLI. In the Program Kit source authoring workspace, read
the exact same-tree schema or supporting resource and use repository-backed
source operations or tests; do not require an installed `program-kit`
executable. If the selected context cannot supply a declared closure item,
stop with a setup blocker; never search assemblies or guess a contract.

## Provider wrapper mapping and drift check

Registered consumer provider wrappers contain only trigger metadata plus exact
`capabilities preflight` and `capabilities read` invocations. The installed
CLI verifies their recorded bytes before returning this definition and renders
each provider into its exact registered root. Legacy roots are migration input
only when the provider contract says so.

The Program Kit source authoring workspace instead refreshes an ignored,
provider-local projection beneath the active provider's registered root only at
a fresh task boundary or on explicit human request. It contains this complete
canonical definition rather than a path reference or consumer CLI invocation.
A changed, missing, stale, partial, or non-exact projection at load time is a
setup blocker.
