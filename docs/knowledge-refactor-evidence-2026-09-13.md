# Knowledge application refactor: implementation evidence

Candidate: 0.12.0 on `codex/repository-sync-coordinator`, based on pushed commit
`cfb60cc3974c4f5458a9814fda0abf6ed39c04fe`. The user approved the combined plan and required
verified evidence. This contributor report records implementation and deterministic findings;
it is not another consumer instruction source or a Release/live acceptance receipt.

## Knowledge authority and coverage

Existing reference owners were extended: dotnet-engineering.md, persistence-profiles.md,
programming-guardrails.md, the .NET technology profile, default-adoption.md,
modularity-and-contracts.md and phase-evidence.md. No parallel best-practices guide was installed.
Primary links checked on 2026-09-13 are retained beside those rules and in the accepted plan.
Product policies such as the PostgreSQL default and operation layout remain explicit Program Kit
decisions; the external sources support API behavior and tradeoffs, not those product choices.

The original research topics are routed through scoped obligations: async completion, Task and
ValueTask, cancellation and streams; locking/atomicity/channels; disposal, DI and memory leases;
LINQ/cardinality/translation; type/default/equality/immutability choices; constructors and Lazy;
method/source quality; controlled time, options, HTTP/file I/O; secure boundaries and observability.
Typed transport/configuration objects and concrete SRP/OCP/LSP/ISP/DIP questions extend the existing
implementation-quality review. Conditional unsafe/interop, lock-free, reload and runtime-code
features require scoped investigation when selected, not mandatory usage in every consumer.

Phase projection selects exact existing headings and hashes their content. Design identifies
applicability, source references and checks; implementation preflight checks current design and
setup; delivery binds current sources, executed JUnit/TRX and attributable review. Missing or
ambiguous section anchors fail. Managed engineering inputs and scoped persistence authorities
participate in freshness. Unrelated future owners' unfinished evidence is excluded from the
current feature's source and materialization scope. Baseline authority remains recorded separately.

Compiler diagnostics and structural checks do not certify SOLID, semantic cohesion, security or
every possible framework usage. These require actual source review and relevant executed behavior.
An accepted not-applicable finding avoids invented mechanisms and unnecessary tests.

## Persistence and upgrade

Canonical bootstrap data-owner intent remains immutable after approval. Server-relational .NET
`auto` resolves to EF/PostgreSQL, explicit alternatives remain visible, and unresolved admission
does not become `none`. Later feature admission supplies provider/test placement, behavior checks
and ten evidence topics without rewriting the approved bootstrap file. An accepted provider
override and transition authority are required for later changes. Sync does not migrate data.

The same resolver and generated central-package aggregate serve bootstrap, setup and upgrade.
Multiple owners merge compatible pins. Actual evaluated package references, central versions,
conditional omissions, disabled CPM, local overrides, provider ownership and private EF Design
tooling are checked. The managed EF tool follows the selected Design pin. Supervisor provisioned
tests omit unused Testcontainers pins. Accepted installed owners survive subsequent upgrades;
blocked transitions preserve their pins and tooling. Untouched authenticated old scaffolds gain
the new import; customized central files remain preserved with a required coherence correction.

Pins exercised: SDK 10.0.202, EF/Design 10.0.11, Npgsql EF provider 10.0.3. The catalog's
Testcontainers.PostgreSql 4.14.0 remains the alternative test provisioning pin. The fictional trial
uses the supervisor's exact PostgreSQL image, recorded in acceptance/services.json. The actual
image reports PostgreSQL 18.6. A user-owned consumer can select another admitted provider.

## Related issue decisions

| Issue | Implemented integration and evidence boundary |
| --- | --- |
| [#16](https://github.com/orbyss-io/program-kit/issues/16) | Existing capability adoption gates remain authoritative. Actual released Forms/JSON, two-shell WebDefaults/JSON and HostedPages probes passed. The complete new live consumer must still prove combined use. |
| [#17](https://github.com/orbyss-io/program-kit/issues/17) | Concrete typed/SOLID review, strict request/tolerant response boundaries, substitution and legitimate static/internal/dynamic exceptions are routed through existing engineering obligations and fixtures. |
| [#18](https://github.com/orbyss-io/program-kit/issues/18) | Operation-owned source roles, independent operation folders, mirrored test ownership, thin composition review and proportional small-operation exceptions are checked. Wire identities are bound to generated OpenAPI. |
| [#19](https://github.com/orbyss-io/program-kit/issues/19) | Existing OpenAPI registration and baseline authority now bind scoped operations, generated hashes, reachable changed schemas, DTO/parser/schema checks, version decisions, old-client/snapshot tests and retirement. A deterministic V1-to-V2 fixture passed. |
| [#20](https://github.com/orbyss-io/program-kit/issues/20) | Foundation and Forms 0.2.0 public mechanisms were verified as dependency inputs. Upgrade preserves consumer changes and renews applicable proof. The historical consumer remains unchanged and no task was resumed or messaged. Publication and consumer handoff remain later decisions. |

API Evolve v1.0.0 was evaluated at upstream commit
`ca528b093120d3e10c50c3a5c6179577e8264852` in
[its repository](https://github.com/Quratulain-bilal/spec-kit-api-evolve/tree/ca528b093120d3e10c50c3a5c6179577e8264852).
The actual installed Spec Kit ExtensionManifest rejected its manifest:
`Missing requires.speckit_version`. Source inspection found Markdown agent commands/hooks,
independent snapshots, after-tasks edits, gates and optional version/tag actions overlapping current
authorities. Decision: do not install this version. Retain useful compatibility questions in the
existing flow. No compatible hook execution was claimed. Reconsideration requires a compatible
verified manifest, useful bounded execution and a single baseline/release authority.

## Executed verification

| Check | Observed result |
| --- | --- |
| Bounded Test-ProgramKit Development | Passed again on the final reviewed changes; log artifacts/knowledge-refactor-development.log. |
| Phase obligations / persistence selection / API proof | 20 / 17 / 13 checks passed, including negative controls and legitimate exceptions. |
| Repository sync / database supervisor | 10 / 4 checks passed. |
| Installed local upgrade | Passed planned-only and materialized sequential upgrades; invalid states rejected before mutation. Log artifacts/refactor-local-upgrade.log. |
| Lifecycle/profile and bootstrap context | Passed installed integration, activation, ownership, external-host boundaries and context freshness. |
| Published analyzer and SDK | Real compiler positive/negative controls passed; 16 runtime engineering cases passed. Evidence artifacts/dotnet-engineering/verification.json and runtime.xml. |
| EF/Npgsql/PostgreSQL | 8 real-provider cases passed, plus actual evaluated CPM positive/conditional negative, exact shared migration deployment from a provider class library, database restart and cleanup. Evidence artifacts/persistence-runtime/verification.json. |
| Released public components | Forms/JSON, actual two-shell WebDefaults/JSON and HostedPages HTTP probes passed; artifacts/public-component-use/8dff232e. |
| Existing release bundle / runnable host pins / knowledge inventory | Targeted checks passed (12 / 11 / 4); no complete Release suite invoked. |

The published Foundation.Analyzers 0.2.0 archive hash is
`145c540ec32fd40bb3ab2a86778bebc71671d43aa24843ab8ba102106261dd1c`.
Its actual diagnostic IDs are ORB1001–ORB1006; stale PK identifiers in the template were corrected.
ORB1002 is a suggestion and establishes its actual argument-count case, not every contextual
method-extraction policy. Scoped suppression and generated code remain supported. CA2012 and
CA2016 are now verified errors. CA2012 controls use an opaque returned ValueTask; a known Task-backed
construction is not an appropriate misuse control. Documentation-meaning review remains separate.

Database cases establish atomic rollback, optimistic contention, stable replay/conflicting identity,
commit-ambiguity handling, provider translation/tenant predicates, durable restart and notification
retry ownership. Commit acknowledgement loss is deliberately injected after a real commit through
the real provider execution strategy; it is not a real network fault. Durable notification ownership
is not an exactly-once external network-delivery guarantee.

## Fresh trial boundary

The acceptance service supplies isolated generated database credentials through the environment,
redacts streams and owns exact container/network cleanup. It uses existing published database and
Foundation images. Consumer releases remain bundles of shells.json, hostsettings.json,
nuplane.settings.json and optional package feeds, with no consumer host DLL/image build.
Independent HTTP and browser acceptance each deploy reviewed EF migrations to a fresh service
before host activation. Host restart retains its database. Normal host startup does not migrate.

All previous paid trials and approved intake records remain historical evidence. Their source
receipts do not authorize this candidate. Prepare a new exact clean-commit development-trial receipt,
then a human-owned full intake. Bootstrap and the first vertical slice need their own one-use
authorizations. The implementation approval starts no paid session. No release was published and
no GitHub issue was closed.

Live token savings, unnecessary reading/retries, combined behavior and useful versus avoidable time
remain unmeasured for this candidate. The live trial must report cached tokens separately, retain
failed attempts and reject cheaper runs that omit required work. Firefox remains unavailable on
this Windows host; CI is authoritative for that browser. The deterministic work does not establish
universal correctness or publication readiness.

## Live finding: assessment gate ef606c1a

The next human-owned trial reached `validate-assessment` and failed with
`Bootstrap decisions have invalid top-level fields (missing=[], unexpected=['persistence'])`.
Intake, assessment/research output budgets and managed profile pins had passed. The authoring schema
already accepted persistence, but governance_state.py retained a separate closed field list. Earlier
resolver/schema tests and packaged installation did not exercise this new field through the actual
assessment gate. The fix derives accepted top-level fields from the existing schema and validates
persistence through its shared definition. Invalid types/profiles and unknown fields still fail;
proposed provider intent does not require implementation evidence at assessment.

Testing the corrected gate against unchanged saved consumer decisions exposed a second contract
inconsistency: explicit anonymous browser `none-v1` was represented by the trial and the existing
profile selection concept, but the gate allowed only authenticated browser profiles. The existing
profile reference and assessment command now distinguish explicit anonymous browsers from non-browser
projects. Browser `none-v1` needs explicit intake/override, rationale and the named adopted choice;
BFF remains the default. `none-v1` assurance fields mean no inherited authenticated-profile assurance,
not absence of HTTP/JSON/assets protections or applicable security evidence.

The actual assessment CLI passes with the user's saved decisions unchanged (SHA256
`f00646bccabc261d204d99658e82ad171dc8652e080c4b0ce92d9d610d81b7d5`). This is read-only diagnostic
validation using corrected maintainer source, not a successful native workflow stage or approval.
The installed consumer, failed run and approvals remain unchanged. Original state/log are also
preserved under artifacts/bootstrap-failure-ef606c1a. No paid recovery was launched.

The real governance gate regression now covers proposed persistence plus explicit anonymous browser
intent, rejects silent anonymous defaults/missing rationale/malformed declarations, and checks that
validation creates no approval or input mutation. Its importlib caller path was repaired to find the
shared sibling module. This bounded validator is promoted from Release-only to Development coverage.
Current governed recovery maps this validator failure back to assessment and research; a normal
resume therefore repeats paid producer work. A read-only diagnostic pass must not be used to edit
the saved stage status or imply that a cost-free validator-only recovery already exists.

Corrected Development and installed sequential upgrade validation passed; logs are
artifacts/assessment-recovery-development.log and artifacts/assessment-recovery-upgrade.log.
