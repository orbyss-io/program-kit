---
artifact-kind: program-kit-design-category
category: diagnostics-and-ai-guidance
status: active
last-updated: 2026-08-01
active-batch: DIA-B04
parent-ledger: DESIGN.md
---

# Program Kit Design — Diagnostics and AI Guidance

## 1. Category objective

Define a stable diagnostic and operation-result protocol that always tells a
human or AI session what happened, whether any trusted effect occurred, why the
operation stopped, and what kinds of next action are permitted. Diagnostics are
part of Program Kit's product contract, not console decoration or exception
text.

This category preserves these accepted boundaries:

- the kernel owns diagnostic truth and non-bypassable admission results
  (`DEC-023`);
- unresolved intent, ambiguous selection, unsupported claims, drift, and
  unavailable exact inputs remain explicit and actionable;
- operation providers must ship stable diagnostic catalogs and
  machine-actionable remediation references (`DEC-033`);
- partial publication is never trusted and interrupted publication remains
  explicit (`DEC-035`); and
- runtime monitoring and automated migration are outside v1 (`DEC-030`).

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `DIA-B01` | `DIA-001`–`DIA-005` | `completed` | Define the universal result envelope, normative rendering, outcomes, categories, and mandatory fields. |
| `DIA-B02` | `DIA-006`–`DIA-008`, `DIA-015`–`DIA-016` | `completed` | Define remediation, agent disposition, documentation links, and resumable input requests. |
| `DIA-B03` | `DIA-009`–`DIA-012` | `completed` | Define catalog compatibility, message evolution, localization, ordering, deduplication, and truncation. |
| `DIA-B04` | `DIA-013`–`DIA-014` | `active` | Define information safety and the last-resort host-failure boundary. |

## 3. Founding requirement

Every Program Kit interaction must return the most meaningful result the system
can honestly provide to the human-led AI session using it. A failure without a
stable category, bounded cause, effect state, and corrective direction is a
product failure even when the process exits nonzero.

This does not mean the CLI may invent an explanation. Unknown causes, internal
faults, redacted details, and indeterminate publication are explicit result
states with their own stable diagnostics.

## 4. Accepted batch: Universal operation results

`DIA-B01` resolves:

- `DIA-001`: whether failures before admission use the same result envelope;
- `DIA-002`: whether machine and human representations are always available;
- `DIA-003`: the closed top-level outcome states;
- `DIA-004`: the diagnostic categories that distinguish responsibility and
  correction paths; and
- `DIA-005`: the mandatory result and diagnostic fields.

The human accepted all five recommendations. They are governed by
`DEC-037`.

### DIA-001 — One result envelope from parse through publication

**Recommendation:** Every public CLI operation returns one versioned Program
Kit operation-result envelope once the host can run, including usage errors,
schema failures, unresolved selection, unavailable providers or inputs,
evaluation failure, drift, publication refusal, cancellation, and internal
faults. Pre-admission failure is not permission to fall back to ad hoc text.

The envelope reports the furthest successfully reached phase and whether the
operation produced no effect, an isolated candidate only, a committed trusted
effect, or an indeterminate effect requiring recovery. An error may never imply
that "nothing changed" unless the effect state proves it.

Help and version commands may use their own stable successful data shapes but
still participate in the public CLI protocol. A process failure before any
envelope can be constructed is handled by the last-resort host boundary in
`DIA-B04`, not silently ignored.

### DIA-002 — Structured results are normative; human output is a projection

**Recommendation:** The structured machine result is canonical protocol truth.
Human-readable output is rendered from the same result and may not add, remove,
or reinterpret semantic facts.
The canonical result excludes observation time, duration, random invocation
identifiers, and other execution metadata. A host may expose such metadata in
an explicitly non-canonical section or separate log channel; it cannot affect
the result digest, diagnostic ordering, or meaning.

Interactive terminals may default to the human rendering. `--output json`
emits exactly one complete JSON result document on standard output with no ANSI
codes, progress, banners, or unstructured logs mixed into it. Diagnostic logs
and progress use a separate channel. Session capabilities and automation use
the structured mode.

Exit codes provide a small documented process-level mapping for shell use; they
are not substitutes for outcome, diagnostic identity, or remediation data.

### DIA-003 — Five closed, action-oriented outcomes

**Recommendation:** V1 has five mutually exclusive top-level outcomes:

1. **`succeeded`** — the requested operation completed; warnings may exist and
   a separate change indicator says whether anything was published.
2. **`needs-input`** — the operation can continue only after identified human or
   external input, selection, or approval is supplied; this is not an internal
   failure.
3. **`blocked`** — an understood rule, incompatibility, conflict, drift,
   unavailable dependency, or invalid request prevents completion. Diagnostics
   identify the exact blocker and correction path.
4. **`cancelled`** — an authorized cancellation was observed and effect state
   reports how far publication progressed.
5. **`faulted`** — Program Kit or a called tool failed outside a declared
   domain result, or effect state cannot be established safely.

There is no top-level `unknown`, `partial-success`, or
`succeeded-with-warnings`. Unknown cause belongs to an honest diagnostic;
candidate or incomplete bytes are never success; warning severity is orthogonal
to outcome.

### DIA-004 — Category identifies the correction boundary

**Recommendation:** Every diagnostic has exactly one primary category from this
closed v1 set:

- **`request`** — CLI shape, supplied intent, or required input is invalid or
  incomplete;
- **`semantic`** — a canonical definition or vocabulary constraint fails;
- **`resolution`** — exact provider, version, profile, dependency, or relation
  selection cannot resolve uniquely and compatibly;
- **`policy`** — authority, approval, invariant, or admission policy refuses the
  requested result;
- **`conformance`** — implementation, evidence, or generated output violates an
  applicable contract or is stale or drifted;
- **`workspace`** — path ownership, collision, publication, or recovery state
  prevents safe materialization;
- **`external`** — a declared tool, package source, service, or environment
  dependency fails outside Program Kit's control; or
- **`internal`** — Program Kit violated an invariant, encountered an undeclared
  condition, or could not classify a fault more precisely.

Category is independent of severity and outcome. For example, unavailable exact
input may be a blocking `external` diagnostic, while ambiguous installed
providers are a blocking `resolution` diagnostic. Providers may add diagnostic
IDs inside their namespace but cannot add top-level categories without a
protocol revision.

### DIA-005 — Results answer state, cause, consequence, and next action

**Recommendation:** Every operation result contains at least:

- result-schema and factory-protocol revisions;
- operation contract identity;
- request digest when parsing reached a canonical request;
- resolved construction identity and lock reference when resolution completed;
- outcome, furthest phase, effect state, and change indicator;
- typed result, candidate, receipt, and evidence references when applicable;
- the ordered diagnostic collection; and
- continuation data only when the outcome supports it.

Every diagnostic contains at least:

- stable authority-qualified diagnostic ID and catalog revision;
- severity, primary category, operation phase, and stable occurrence key;
- typed subject references and applicable rule, contract, and profile
  references;
- a stable message key with structured, non-secret parameters;
- bounded cause and consequence data;
- expected and observed values when safe and applicable;
- machine-actionable remediation references and permitted next-action kinds;
  and
- related evidence and documentation references when applicable.

Fields that cannot safely or truthfully be populated are explicitly absent or
redacted according to schema; they are not filled with guessed values. Raw
exception text, stack traces, absolute protected paths, and arbitrary provider
prose are never the machine contract.

### DIA-B01 delivery boundary

The first CLI needs one result model and JSON Schema, one serializer, one human
renderer, a documented exit-code mapping, and fixtures covering each outcome
and category. Machine-mode snapshot tests must prove that standard output
contains one parseable result and no incidental text.

V1 does not yet need localization, a resumable continuation store, automatic
patch application, a documentation portal, or the final catalog compatibility
policy. Those belong to later diagnostics batches.

## 5. Accepted batch: Remediation and session control

`DIA-B02` resolves:

- `DIA-006`: when diagnostics may supply exact commands or patches;
- `DIA-007`: which corrections an AI may perform without renewed approval;
- `DIA-008`: how a result tells the session to retry, ask, repair, or stop;
- `DIA-015`: how diagnostics resolve to rules, schemas, contracts,
  documentation, and any applicable future migration; and
- `DIA-016`: whether missing input is a first-class resumable continuation.

The human accepted all five recommendations. They are governed by
`DEC-038`.

### DIA-006 — Remedies are typed actions, never executable prose

**Recommendation:** A diagnostic may offer one or more typed remediation action
descriptors. Each descriptor declares an authority-qualified remediation ID,
action kind, purpose, exact preconditions, effect class, bounded targets,
required authority or approval, expected postcondition, and the result phase to
retry after successful completion.

An exact CLI suggestion is represented as a Program Kit request or executable
plus argument array, never as a shell command string copied from diagnostic
text. A proposed file change is an immutable candidate or patch reference with
a digest, exact target preconditions, ownership checks, and preview. Suggested
values never contain secrets.

Program Kit supplies an exact action only when it can prove the action is
bounded and applicable. Otherwise it returns a structured explanation of the
missing decision or investigation. A remediation descriptor is a proposal, not
execution authority, and its presence never makes a dangerous action safe.

### DIA-007 — Automation consumes existing authority and never creates it

**Recommendation:** Every remediation declares whether automation is
permitted, requires approval, or is prohibited under the applicable policy. An
AI session may execute it without renewed approval only when the kernel
independently verifies that the current authority grant covers the exact action
and targets, all preconditions still match, and the action stays within the
already accepted request.

Read-only inspection, validation, explanation lookup, isolated candidate
creation, and bounded retry of a declared transient failure may normally be
automated. A live mutation may be automated only when the human or selected
policy already authorized that exact mutation class; "safe" diagnostics do not
imply consent.

A new human approval is required for identity-forming intent or definition
changes, provider/version/profile selection, new dependencies, policy or
exception changes, gate suppression, ownership reclassification, or any
trusted publication outside the current grant. The later Governance category
may refine approval policy, but diagnostics can never elevate it. Instructional
text and an AI's confidence are not authority.

### DIA-008 — One primary disposition tells the session what to do next

**Recommendation:** Every result has exactly one primary session disposition
from this closed v1 set:

- **`complete`** — the request is finished; report the result and stop;
- **`retry`** — repeat the declared phase only under exact stated conditions;
- **`provide-input`** — satisfy a typed continuation input schema;
- **`request-approval`** — obtain the identified authority grant;
- **`repair`** — perform one permitted remediation and then invoke a fresh
  evaluation or construction request;
- **`revise`** — change authoritative intent, selection, or definition, which
  creates a new identity and may require approval; or
- **`stop`** — no safe progress exists inside the current request.

The result may list ordered alternative remediation actions, but the primary
disposition cannot be ambiguous. `retry` declares its condition, retryable
phase, attempt limit, and delay policy so an agent cannot loop indefinitely.
Disposition guides control flow but grants no authority.

### DIA-015 — Explanations are exact resources, with optional human links

**Recommendation:** Diagnostic, remediation, rule, schema, operation-contract,
provider, profile, evidence, and documentation references use exact
authority-qualified identities and revisions. Optional web URLs are human
conveniences, not the only source of meaning.

The CLI provides a structured diagnostic-explanation lookup backed by the exact
selected catalog, so an AI session can resolve a diagnostic offline to its
definition, parameters, causes, consequences, actions, related contracts, and
examples. The core result itself retains enough information to remain
actionable when extended documentation cannot be reached.

A migration reference is included only when an exact applicable migration is
actually available in a future scope. V1 does not suggest generic migration or
link to nonexistent remediation under the deferred migration boundary.

### DIA-016 — `needs-input` returns a stateless continuation artifact

**Recommendation:** `needs-input` is a first-class non-success outcome that
returns a canonical continuation-request artifact. It identifies the original
operation and request digest, furthest phase, missing input schema, allowed
choices and constraints, reason each value is needed, required authority,
completed candidate or evidence references, and every freshness precondition.

The human or AI resubmits that artifact with explicit answers. The CLI keeps no
hidden conversational or server-side continuation state. On resume, the kernel
revalidates the continuation digest, authority, exact inputs, lock, workspace,
and evidence. Changed preconditions produce a stale-continuation diagnostic
rather than reusing an unsafe decision.

Identity-forming answers create the corresponding new construction identity and
resolution lock and trigger normal approval rules. Secret answers are supplied
through declared secure references or input channels and are never embedded in
the continuation artifact. No trusted live publication occurs merely because
input is requested.

When several independent missing values are already known, one continuation
schema requests them together. Program Kit must not force an AI through a
serial question loop merely because the CLI discovered fields one at a time.

### DIA-B02 delivery boundary

The first CLI needs the typed remediation descriptor, primary disposition,
structured explanation lookup, and canonical continuation-request artifact.
Fixtures prove bounded retry, approval refusal, stale continuation, safe
argument representation, and multi-field input collection.

V1 does not need arbitrary shell execution, automatic patch application, a
hidden continuation database, or a general autonomous-agent policy engine.

## 6. Accepted batch: Catalog compatibility and bounded rendering

`DIA-B03` resolves:

- `DIA-009`: whether diagnostic IDs are permanent or only catalog-major stable;
- `DIA-010`: how message text evolves independently from machine meaning;
- `DIA-011`: whether localization belongs in v1; and
- `DIA-012`: deterministic ordering, deduplication, grouping, and safe
  truncation.

The human accepted all four recommendations. They are governed by
`DEC-039`.

### DIA-009 — A diagnostic ID's meaning is permanent; catalogs still version

**Recommendation:** A diagnostic ID is authority-qualified and never reused for
a different trigger condition or violated invariant. It may be deprecated,
retired, or linked to a replacement, but its recorded meaning remains permanent
across catalog major versions. Provider diagnostic IDs live in their provider's
namespace and cannot collide with kernel or other-provider IDs.

Every composed diagnostic catalog has an exact identity, immutable revision,
schema/protocol version, and content digest selected by the Program Kit
distribution and operation lock. A catalog revision may add IDs, templates,
remedies, examples, or metadata. A breaking schema change or removal requires a
new catalog major version, but even a major version cannot recycle an old ID or
silently redefine it.

Compatibility labels help clients understand catalog evolution; execution and
explanation always use the exact selected catalog. An unknown diagnostic ID is
preserved as structured unknown provider data and never guessed from its text.

### DIA-010 — Machines consume identity and fields, never rendered wording

**Recommendation:** Each diagnostic separates its stable ID, typed fields,
message key, structured parameters, and catalog-owned templates. Automation
branches only on the ID, category, outcome, disposition, and typed fields; it
never parses a rendered sentence.

Meaning-neutral wording, grammar, examples, and documentation may improve under
the same diagnostic ID in a new exact catalog revision. Severity defaults,
remediation options, and links may also evolve only through an explicit catalog
revision. A material change to the trigger, violated invariant, primary
category, subject semantics, or consequence requires a new diagnostic ID with
an explicit replacement relation.

Every human rendering includes the stable diagnostic ID so copied output can be
resolved without relying on its exact prose.

### DIA-011 — English is the v1 rendering; localization remains pluggable

**Recommendation:** V1 ships one invariant structured protocol and one English
human rendering. Localization is allowed later through exact versioned language
resources keyed by catalog identity, diagnostic ID, message key, and typed
parameters. Localized prose never changes machine meaning or canonical result
data.

A future renderer reports requested and effective locale and falls back
explicitly to the catalog's invariant English template when a translation is
missing. Program Kit never uses the operating-system locale to alter machine
fields, ordering, parsing, numbers, dates, paths, or generated bytes.

V1 does not need translation infrastructure or localized diagnostic catalogs.
Deferring them avoids blocking the CLI while keeping localization compatible
with the protocol.

### DIA-012 — Full canonical diagnostics; bounded deterministic views

**Recommendation:** Program Kit produces one complete canonical diagnostic
collection for the operation. Its order is deterministic by:

1. whether the diagnostic determines outcome, effect state, or primary
   disposition;
2. operation-phase ordinal;
3. severity rank;
4. category ordinal;
5. canonical subject identity;
6. diagnostic ID; and
7. stable occurrence key.

Exact duplicate occurrences share the same diagnostic ID, subject, rule,
structured parameter fingerprint, and cause fingerprint. They collapse into
one group with an occurrence count and combined evidence references. Distinct
subjects, observed values, rules, or causes are never deduplicated merely
because their rendered messages match.

A result envelope or human renderer may expose a bounded view, but truncation
is explicit. It reports total and returned counts, omitted counts by severity
and category, grouping information, the full collection's digest and artifact
reference, and a stable content-bound cursor for further structured retrieval.
Every cause that determines the top-level outcome, effect state, or disposition
must remain represented in the bounded view, at least through a lossless group
summary.

Truncation never changes outcome, effect state, admission, or disposition and
never silently drops diagnostics. Pagination is over the immutable canonical
collection, not a mutable live query or unstable numeric offset.

### DIA-B03 delivery boundary

The first CLI needs one exact core catalog, validation for unique IDs and typed
message parameters, an English renderer, canonical ordering and duplicate
grouping, and an explicit bounded-view fixture with content-bound retrieval of
the full collection.

V1 does not need localized resources, remote catalog discovery, diagnostic
telemetry, or compatibility-range selection.

## 7. Active batch: Information safety and host failure

`DIA-B04` resolves:

- `DIA-013`: how diagnostics avoid leaking secrets, protected paths, topology,
  and unauthorized existence information; and
- `DIA-014`: when an unexpected crash can and cannot become a structured
  last-resort host diagnostic.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### DIA-013 — Disclosure is schema-governed and fails closed

**Recommendation:** Every diagnostic parameter, subject reference, evidence
reference, and remediation value declares a disclosure classification and
permitted rendering. The kernel enforces a non-bypassable minimum; an
applicable policy may restrict disclosure further but cannot authorize secret
values in ordinary diagnostic output.

Secret values, credentials, tokens, protected environment values, raw command
lines containing secrets, and secret-derived hashes are never emitted.
Workspace paths are repository-relative when disclosure is permitted;
otherwise diagnostics use logical subject identities. Absolute user, temporary,
cache, credential-store, and protected-system paths are omitted or redacted.
Unauthorized resources use non-enumerating results such as
`not-found-or-not-authorized` rather than confirming existence.

Every redaction is structured with a safe reason and governing policy or
classification reference. It never includes a reversible placeholder or
stable secret fingerprint. Machine JSON, human rendering, verbose mode, and
debug mode obey the same disclosure floor; structured output is not a privileged
leak channel.

External tool output, provider exceptions, compiler messages, and logs are
untrusted input. Program Kit parses only declared structured adapters, applies
disclosure policy to typed fields, and otherwise reports a bounded sanitized
summary with a separately authorized evidence reference. It never copies raw
stdout, stderr, exception messages, environment dumps, or stack traces into the
operation-result contract.

A catalog or provider whose diagnostic parameter schema omits disclosure
classification fails conformance. Unknown values are withheld rather than
rendered optimistically.

### DIA-014 — A minimal fallback result exists whenever the process still can

**Recommendation:** The CLI host wraps every recoverable command path and
converts an unexpected kernel, provider, adapter, serializer, or external-tool
failure into the most specific available structured `faulted` result. The
fallback reports a stable host-fault diagnostic, the furthest known phase, a
safe cause category, and an effect state derived from publication records. It
never asserts `none` when state cannot be proven; it reports `indeterminate` and
directs recovery instead.

The last-resort result uses a tiny embedded schema, catalog entry, disclosure
filter, and serializer that do not depend on provider loading, workspace
schemas, normal rendering, or the failing diagnostic pipeline. JSON mode
buffers the complete document before writing it so a recoverable exception
cannot intentionally stream malformed partial JSON. Human fallback output is a
projection of the same minimal result.

Raw exception and stack information may be captured only in a separately
authorized protected evidence artifact with its own disclosure controls. The
ordinary result exposes a safe reference when one was successfully created.
The next invocation inspects any publication journal before permitting further
construction.

Program Kit cannot guarantee an envelope when the process cannot start, is
forcibly terminated, suffers an unrecoverable runtime or operating-system
failure, runs out of resources required by the fallback, or cannot write the
selected output channel. This is an explicit availability boundary, not a
missing diagnostic case. No catch-all may conceal such limits or claim that
workspace state is safe.

### DIA-B04 delivery boundary

The first CLI needs parameter disclosure metadata, repository-relative/logical
subject rendering, redaction fixtures for secrets and protected paths,
sanitized external-failure fixtures, and a minimal top-level host fallback.
Fault injection before, during, and after publication must prove honest effect
state and recovery guidance.

V1 does not need crash-dump collection, remote telemetry, a privileged debug
mode, or a general data-loss-prevention engine.

## 8. Revision record

- Created after Determinism and Generated Artifacts closed under `DEC-036`.
- Made structured guidance to human-led AI sessions a product-level protocol
  concern rather than an optional rendering concern.
- Activated `DIA-B01` for the universal operation-result foundation.
- The human accepted `DIA-B01` in full under `DEC-037`.
- Established one universal structured result envelope, five closed outcomes,
  eight diagnostic categories, explicit effect state, and mandatory actionable
  diagnostic data.
- Completed `DIA-B01` and activated `DIA-B02` for remediation, session control,
  explanation lookup, and resumable input.
- The human accepted `DIA-B02` in full under `DEC-038`.
- Established typed non-authorizing remedies, authority-aware automation, one
  primary session disposition, exact offline explanation resources, and
  stateless continuation artifacts with full freshness revalidation.
- Prohibited raw shell remedies, inferred authority, hidden continuation state,
  and unbounded agent retry.
- Completed `DIA-B02` and activated `DIA-B03` for catalog compatibility and
- The human accepted `DIA-B03` in full under `DEC-039`.
- Made diagnostic meaning permanent per authority-qualified ID while retaining
  exact versioned catalogs, machine-independent message rendering, and a
  pluggable but deferred localization boundary.
- Required complete canonical diagnostic collections with deterministic
  ordering, exact duplicate grouping, and explicit retrievable bounded views.
- Completed `DIA-B03` and activated final Diagnostics batch `DIA-B04` for
