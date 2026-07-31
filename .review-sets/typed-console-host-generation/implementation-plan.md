# Typed Console host generation implementation plan

State: awaiting exact human approval.

This plan implements only the exact canonical `architecture-design.json` bytes
identified by `implementation-plan.json`. Any material change to ownership,
framework, binding, validation, integrity, activation, or authority requires a
new design and renewed human approval.

## Global authority and completion rules

- Work only in the Program Kit repository on the human-selected branch.
- Integrate the completed reusable C# build-gates change before implementation
  source mutation.
- Re-read the exact approved design, plan, approval, current source, and
  applicable guidance before every dependent work unit.
- Keep each work unit buildable, reviewable, tested, committed, and pushed.
- Do not publish packages, create a release, deploy, modify JTest, activate
  distributable capabilities in the authoring workspace, or weaken a gate.
- Stop on a material architectural deviation, missing approval, conflicting
  shared-build contract, unavailable exact dependency, or required authority
  beyond this plan.

## Requirements

| ID | Required outcome |
| --- | --- |
| `PKTCH-R001` | Open Console has language-neutral schema and implementation ownership with no CLR or Spectre vocabulary. |
| `PKTCH-R002` | An explicit .NET binding document maps every command to verified CLR request, handler, optional validator, feature, and default contracts. |
| `PKTCH-R003` | Consumer contracts are verified against exact reference-assembly metadata without loading or executing consumer code. |
| `PKTCH-R004` | Console generation emits a complete deterministic executable project using exact Spectre and CShells package versions. |
| `PKTCH-R005` | Generated commands enforce document validation, optional consumer validation, and handler invocation in the fixed host-owned order. |
| `PKTCH-R006` | Parsing, help, completion, diagnostics, cancellation, and exit codes conform to Open Console through the pinned .NET projection profile. |
| `PKTCH-R007` | Exactly one Console shell feature and exact handler/validator registration cardinality fail closed through explicit DI composition. |
| `PKTCH-R008` | Every generated host tree is sealed and offline-verifiable through a host-kind-neutral manifest and external anchor. |
| `PKTCH-R009` | Build and publication reject generated drift without adding runtime source-tree verification. |
| `PKTCH-R010` | Refresh is deterministic and atomic; explicit repair quarantines drift and regenerates from authoritative inputs. |
| `PKTCH-R011` | `maintain-software` reuses the same backed completion profiles as full implementation and records coherent reversible history. |
| `PKTCH-R012` | Program Kit product capabilities are inert, installable, version-locked, drift-verifiable, and forbidden from authoring-workspace activation. |
| `PKTCH-R013` | A real isolated consumer proves typed commands, validation, exit codes, determinism, integrity, repair, and capability installation end to end. |

## Coordination prerequisite

Satisfied before this plan was materialized: the reusable C# build-gates change
is integrated into `main`, Architecture Design `2.0.0`, Planning `3.0.0`, and
the static-conformance disposition contract are current source truth. This plan
selects the existing private Program Kit gate, current build-spine activation
matrix, and exhaustive verification profile. Revalidate their exact recorded
digests at implementation preflight and stop on drift or material conflict.

## PKTCH-W010 — Language-neutral Open Console ownership

**Required outcome:** establish neutral Open Console schema and source
ownership, including logical value types, canonical defaults, parsing, help,
completion, streams, and host exit-code roles.

**Allowed edits:** neutral schema registry and schema files; new Open Console
project; existing Open Console readers, validators, fixtures, documentation,
solution and package registration required by the move.

**Verification:** schema and semantic validation; canonical serialization;
round-trip fixtures; no CLR, Spectre, CShells, or project vocabulary in the
normative document; focused unit and schema conformance tests.

**Stop conditions:** stop if neutral ownership requires narrowing the document
to one host framework, if an existing schema consumer cannot be updated in the
same unit, or if a cross-language representation decision remains unresolved.

## PKTCH-W020 — .NET binding contract

**Depends on:** W010.

**Required outcome:** add the versioned .NET binding schema and canonical model
with explicit generated symbols, structured CLR types, mandatory default
dispositions, constructor mappings, contracts, project identity, and exact
reference-assembly digest.

**Allowed edits:** .NET schemas and binding subsystem; canonical serializers;
validators; diagnostics; unit fixtures and documentation.

**Verification:** accepted binding round trips; one-to-one command
reconciliation; symbol collision, type, nullability, default, constructor,
handler, validator, feature, and missing-binding rejection.

**Stop conditions:** stop if any semantic mapping must be guessed, executable
code would enter the binding document, or Open Console would gain CLR meaning.

## PKTCH-W030 — Metadata inspection and candidate compilation

**Depends on:** W020.

**Required outcome:** verify the exact binding against digest-checked consumer
metadata and compile isolated generated candidates against the exact reference
assembly without loading consumer code or invoking MSBuild.

**Allowed edits:** .NET Console binding, contracts, compilation, metadata,
diagnostic, and source-gate areas; test assemblies and fixtures.

**Verification:** valid contract proof plus malformed metadata, digest drift,
missing types, accessibility, generic/nullability/signature mismatch,
forbidden constructor dependency, stale reference, and source-injection tests.

**Stop conditions:** stop if verification requires `Assembly.Load`, consumer
execution, ambient dependency resolution, arbitrary MSBuild, or relaxed source
gates.

## PKTCH-W040 — Deterministic Spectre projection and generated project

**Depends on:** W030.

**Required outcome:** replace Console generation with the immutable projection
and per-file renderers for a complete executable host using exact
Spectre.Console 0.55.0, Spectre.Console.Cli 0.55.0, and CShells 0.0.28
references.

**Allowed edits:** DotNet Console generation; package versions; generated host
project and source renderers; generation coordinator and results; Console
fixtures, unit tests, documentation, and solution registration.

**Verification:** candidate compilation; deterministic repeated generation;
file-layout goldens; command trie and settings/request mapping; no second
parser, untyped option dictionary, runtime generator dependency, absolute path,
timestamp, or random byte.

**Stop conditions:** stop if the pinned Spectre version cannot represent an
accepted document shape, if a template engine or monolithic renderer becomes
necessary, or if API/Worker behavior changes outside the approved integrity
boundary.

## PKTCH-W050 — CShells composition and invocation lifecycle

**Depends on:** W040.

**Required outcome:** compose exactly one Console feature, audit exact service
registration cardinality, resolve through one invocation scope, and implement
the fixed validation/request/handler lifecycle with cancellation and shutdown.

**Allowed edits:** generated Console composition, service audit, command and
lifecycle renderers; consumer fixture feature and services; focused unit and
process tests.

**Verification:** zero/one/duplicate feature, handler, and validator cases;
wrong lifetime and registration shape; forbidden DI-aware constructors; no
provider duplication; generated validation before optional consumer validation;
handler not invoked after failure.

**Stop conditions:** stop if composition requires scanning, reflection-based
registration, a service locator, more than one feature, or consumer knowledge
of Spectre/generated types.

## PKTCH-W060 — Parsing, help, completion, and exit fidelity

**Depends on:** W050.

**Required outcome:** freeze the pinned Spectre projection behavior and
generated information protocol against Open Console, including stable
diagnostics and handler result preservation.

**Allowed edits:** projection profile, settings validation, command
configuration, help and completion generation, invocation-outcome handling,
process fixtures, goldens, and documentation.

**Verification:** real-process matrix for case, equals syntax, terminator,
unknowns, aliases, duplicates, required and repeated values, invariant native
types, defaults, help, completion, validator messages, cancellation, internal
failure, and portable handler exit codes.

**Stop conditions:** stop if fidelity needs a hidden executable parser,
undocumented built-ins, dynamic completion, or a change to Open Console that is
not language neutral.

## PKTCH-W070 — Host-kind-neutral generated-output integrity

**Depends on:** W040.

**Required outcome:** add neutral manifest and external-anchor schemas, sealing,
offline verification, safe path handling, atomic output transactions, recovery,
and `dotnet verify-host` for API, Console, and Worker generated roots.

**Allowed edits:** neutral integrity schemas and project; DotNet generation
publication; CommandLine descriptor, operation, composition, diagnostics, and
documentation; host fixtures and conformance tests.

**Verification:** immediate verify success; modified, missing, unexpected,
unsafe, symlink/reparse, malformed manifest, missing/mismatched anchor,
transaction recovery, determinism, and all-file diagnostics.

**Stop conditions:** stop if a generated file remains outside digest coverage,
consumer-owned paths are captured, verification requires regeneration/network,
or coordinated self-hash handling is ambiguous.

## PKTCH-W080 — Refresh, repair, build, and publication integration

**Depends on:** W060 and W070.

**Required outcome:** add the generation request, `dotnet refresh-host`,
preview, optional approved consumer build, explicit repair/quarantine, private
build verification package, compile-time attestation, and publication checks.

**Allowed edits:** generation request and refresh orchestration; integrity
transactions; approved build-profile integration; generated project/build
package; local publication; command grammar/docs; unit and conformance tests.

**Verification:** absent/create, valid/no-change, valid/change, drift/refuse,
drift/repair, deterministic preview, quarantine recovery, build rejection,
publication rejection, no runtime source verification, and frozen Program Kit
operation exit codes.

**Stop conditions:** stop if refresh silently erases drift, adopts generated
edits, executes consumer build without explicit authority, auto-upgrades
Program Kit, or duplicates the reusable C# build-gate mechanics.

## PKTCH-W090 — Shared maintenance completion profiles

**Depends on:** W080.

**Required outcome:** package inert shared procedures for source review,
affected-output refresh, integrity, build/test selection, separately authorized
publication, evidence, diff review, coherent commit, and push.

**Allowed edits:** non-discoverable capability supporting resources; existing
implementation capability references; profile schemas/manifest; capability
bundle verification and isolated fixtures.

**Verification:** both full implementation and incremental maintenance resolve
the same exact profile bytes; profiles cannot activate or grant authority; no
hook, watcher, autonomous loop, provider binding, or duplicated procedure body.

**Stop conditions:** stop if a profile becomes independently invokable, grants
authority, duplicates a backed implementation, or requires activation in the
authoring workspace.

## PKTCH-W100 — Installable maintain-software capability and standard

**Depends on:** W090.

**Required outcome:** register and package `maintain-software`, add the bounded
route to `develop-software`, strengthen Program Kit capability authoring so all
product capabilities are distributable and authoring-inert, and prove isolated
consumer initialization.

**Allowed edits:** canonical capability definitions; existing Codex and Claude
adapter templates; capability index/navigation/catalog; bundle manifest and
content package; initializer policy; ownership locks; conformance fixtures and
tests.

**Verification:** canonical completeness; thin-wrapper pointers; no copied rule
bodies; exact bundle digests; authoring-workspace deny; no global writes;
isolated initialization; drift verification; explicit Program Kit upgrade
approval; unavailable status until all backing passes.

**Stop conditions:** stop if the capability can trigger accidentally, work
without a human request, bypass design for material changes, auto-upgrade,
activate while authored, or write outside the selected consumer workspace.

## PKTCH-W110 — Integrated consumer proof and closure

**Depends on:** W080 and W100.

**Required outcome:** prove the complete design through an isolated consumer
with `run`, `validate`, and `describe`, typed requests, three handlers, one
optional validator, one feature, generated host, refresh/integrity evidence, and
maintenance history.

**Allowed edits:** typed Console conformance fixture; test harnesses; generated
expected bytes; docs; review validation and implementation-evidence artifacts.

**Verification:** locked restore; source/analyzer gates; full unit and
conformance suites; actual child processes; deterministic regeneration; tamper
matrix; repair; build/publication rejection; capability package/initialization;
secret/path scan; reviewed changed-file inventory.

**Stop conditions:** stop on any failing required gate, nondeterminism, active
authoring capability, incomplete evidence, package publication requirement, or
material design deviation.

## Requirement trace

| Requirement | Work units |
| --- | --- |
| `PKTCH-R001` | W010, W060, W110 |
| `PKTCH-R002` | W020, W030, W110 |
| `PKTCH-R003` | W030, W110 |
| `PKTCH-R004` | W040, W110 |
| `PKTCH-R005` | W050, W060, W110 |
| `PKTCH-R006` | W060, W110 |
| `PKTCH-R007` | W050, W110 |
| `PKTCH-R008` | W070, W080, W110 |
| `PKTCH-R009` | W080, W110 |
| `PKTCH-R010` | W070, W080, W110 |
| `PKTCH-R011` | W090, W100, W110 |
| `PKTCH-R012` | W100, W110 |
| `PKTCH-R013` | W110 |

## Final completion

After W110, review the exact final diff and evidence, commit and push the
completed work unit, and ensure `main` contains the reviewed commits. Report
the final commit identity and changed-file list. Do not publish packages or
claim a Program Kit release.
