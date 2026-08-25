# Program Kit architecture

## Purpose

This project owns the reusable method for turning a user-provided initial design into a governed Spec Kit repository. It does not own any consuming application's architecture.

## Components

| Component | Responsibility |
|---|---|
| Workflow | Orders bootstrap activities and human approval gates. |
| Extension commands | Give agents deterministic responsibilities and output contracts. |
| Extension hooks | Make architecture validation part of the normal Spec Kit lifecycle. |
| References | Define generic policies and technology-triggered guardrails. |
| Bundle | Pins and distributes the tested component set. |
| Test harness | Validates source manifests and builds a reproducible artifact. |
| Governance-state validator | Revokes stale constitution authority, hash-binds human ratification, and validates specification-roadmap readiness. |

## Dependency direction

The workflow depends on command IDs exposed by the extension and one core Spec Kit command. Commands
depend on reference documents and the fixed-path governance-state validator, but references do not
depend on Spec Kit runtime behavior. The bundle composes components and adds no behavior.

The bootstrap invokes Spec Kit's core constitution command as the canonical writer. Program Kit owns
the surrounding Draft/Ratified state machine, dedicated human gate, exact-content hash, and readiness
checks because the core command does not itself represent human ratification. The ratified
constitution governs architecture, ADRs, the specification roadmap, feature specifications, plans,
tasks, implementation, and verification.

Vertical slices are the default delivery unit. Bounded contexts and modules own domain language,
contracts, and data; features are runtime composition units; shells are runtime isolation contexts;
and endpoints are transport adapters. The generic method defines those boundaries while technology
profiles map them to language and framework mechanisms.

Third-party extensions are evaluated by the workflow and recorded in the consuming project's tooling decision record. They are not dependencies of this source project unless a later ADR accepts them as universally required.

## Trust boundary

Workflow prompts and initial-design content are untrusted inputs. They never flow directly into a
workflow shell step. Hooks invoke agent commands whose instructions require explicit approval for
destructive or externally publishing actions. The packaged Python governance-state validator accepts
only fixed project-relative paths and a literal ratification verdict; it does not execute user input,
network calls, or external processes.
