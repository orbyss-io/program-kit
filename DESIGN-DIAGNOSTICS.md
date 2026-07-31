---
artifact-kind: program-kit-design-category
category: diagnostics-and-ai-guidance
status: active
last-updated: 2026-08-01
active-batch: DIA-B01
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
| `DIA-B01` | `DIA-001`–`DIA-005` | `active` | Define the universal result envelope, normative rendering, outcomes, categories, and mandatory fields. |
| `DIA-B02` | `DIA-006`–`DIA-008`, `DIA-015`–`DIA-016` | `queued` | Define remediation, agent disposition, documentation links, and resumable input requests. |
| `DIA-B03` | `DIA-009`–`DIA-012` | `queued` | Define catalog compatibility, message evolution, localization, ordering, deduplication, and truncation. |
| `DIA-B04` | `DIA-013`–`DIA-014` | `queued` | Define information safety and the last-resort host-failure boundary. |

## 3. Founding requirement

Every Program Kit interaction must return the most meaningful result the system
can honestly provide to the human-led AI session using it. A failure without a
stable category, bounded cause, effect state, and corrective direction is a
product failure even when the process exits nonzero.

This does not mean the CLI may invent an explanation. Unknown causes, internal
faults, redacted details, and indeterminate publication are explicit result
states with their own stable diagnostics.

## 4. Active batch: Universal operation results

`DIA-B01` resolves:

- `DIA-001`: whether failures before admission use the same result envelope;
- `DIA-002`: whether machine and human representations are always available;
- `DIA-003`: the closed top-level outcome states;
- `DIA-004`: the diagnostic categories that distinguish responsibility and
  correction paths; and
- `DIA-005`: the mandatory result and diagnostic fields.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

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

## 5. Revision record

- Created after Determinism and Generated Artifacts closed under `DEC-036`.
- Made structured guidance to human-led AI sessions a product-level protocol
  concern rather than an optional rendering concern.
- Activated `DIA-B01` for the universal operation-result foundation.
