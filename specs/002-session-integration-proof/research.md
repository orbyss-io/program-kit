# Research: Independent CLI Distribution and AI-Session Integration Proof

**Feature**: `002-session-integration-proof`
**Date**: 2026-08-01
**Status**: Complete — no unresolved technical clarifications

## Decision 1: Use Codex's documented CLI-plus-skill pattern

**Decision**: The first real provider adapter will project a repository-scoped
Codex skill that invokes an exact independently installed `program-kit` command.
The command remains a normal CLI, and Codex reaches it through its existing
shell capability. The adapter will not claim that Codex registered a new native
tool type.

**Rationale**: OpenAI's current Codex guidance explicitly recommends an
installed command plus a companion skill for reusable CLIs. The skill records
when to invoke the command, what to run first, how to keep output bounded, and
which writes require approval. Codex discovers repository skills from
`.agents/skills` between the current directory and repository root. This is the
smallest current surface that tests the intended human-led AI workflow without
introducing a server protocol.

**Sources**:

- [Create a CLI Codex can use](https://learn.chatgpt.com/use-cases/agent-friendly-clis)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)

**Alternatives considered**:

- A bundled MCP server: rejected for this feature because the CLI already has a
  local structured interface and MCP would add transport, server lifecycle, and
  another security boundary before they have demonstrated value.
- A Codex plugin: deferred. Plugins are the documented distribution layer for
  reusable skills and optional MCP connections, but direct repository skills
  are the documented workspace-local authoring and discovery surface needed by
  this proof.
- `AGENTS.md` instructions only: rejected because durable repository conventions
  must not be conflated with a focused, independently identifiable session
  capability.
- An undocumented Codex CLI-tool registry: rejected because no current official
  surface supports that claim.

## Decision 2: Keep canonical meaning separate from the Codex projection

**Decision**: A provider-neutral, versioned session-integration definition will
be canonical. It will link existing Program Kit operation contracts and define
authority, effect classes, typed result handling, diagnostic behavior, and the
minimum guidance a session must preserve. The Codex skill and its optional UI
metadata are deterministic projections of that definition.

**Rationale**: Provider-local front matter, paths, invocation syntax, reload
behavior, and skill metadata are integration mechanics. Making them canonical
would prevent another provider from preserving the same Program Kit meaning
through a different surface. Each projection therefore records the canonical
definition digest and adapter identity from which it was generated.

**Alternatives considered**:

- Make the Codex `SKILL.md` source truth: rejected because it would make the
  canonical product model provider-specific.
- Create one lowest-common-denominator instruction document: rejected because
  it would either leak provider vocabulary into the core or weaken mandatory
  authority and diagnostic behavior.
- Copy schemas into each adapter: rejected because copied contracts can drift
  and falsely appear current.

## Decision 3: Package the CLI as one exact .NET tool artifact

**Decision**: `ProgramKit.Cli` will be packable as the exact
`Orbyss.ProgramKit.Cli` .NET tool, with command name `program-kit` and package
version matching the CLI's reported version (`1.0.0-alpha.1` for this slice).
The reference proof installs it into a workspace-local tool directory from an
explicit local feed.

**Rationale**: The .NET SDK already supports exact version selection and an
isolated `--tool-path`. A local research pack with SDK `10.0.302` proved that the
tool package contains the CLI, all current project-reference assemblies, and
locked third-party runtime dependencies. A clean `dotnet tool install` from the
local feed then invoked `program-kit version --format json` successfully from
the installed path. No separate package family is required for the internal
projects.

The package is an external-tool output. Its observed bytes receive an exact
digest, but cross-environment byte identity is not claimed. The integration
record binds package ID, version, source identity, package digest, installed
executable digest, and reported CLI version.

**Alternatives considered**:

- Global tool installation: rejected because it creates ambient version and
  scope conflicts and cannot provide workspace-local ownership.
- A repository project reference or `dotnet run`: rejected because the consumer
  proof must not contain or depend on Program Kit source.
- Self-contained archives: deferred because .NET tool packaging already proves
  the distribution boundary with fewer formats and no new release mechanism.
- Separately package every Program Kit assembly: rejected because the tested
  tool package already includes the complete executable closure.

## Decision 4: Treat CLI acquisition and session registration as separate stages

**Decision**: The reference bootstrap first acquires the exact CLI into a
workspace-local external tool directory. The installed CLI then performs
`session explain`, `session install`, `session verify`, and `session remove`.
The session integration records but does not own or uninstall the independently
acquired CLI.

**Rationale**: A CLI cannot safely guarantee a structured Program Kit result
before it exists or can start. Keeping acquisition separate makes the bootstrap
boundary honest and lets other distribution mechanisms deliver the same CLI
later. Session removal therefore removes only admitted provider projections and
leaves the independently managed CLI artifact intact.

**Alternatives considered**:

- Make `program-kit session install` install its own executable: rejected as a
  circular bootstrap and an unverifiable pre-start promise.
- Have a provider adapter download the CLI: rejected because provider
  installation must not imply CLI selection, trust, or authority.
- Delete the CLI during session removal: rejected because the installation
  record cannot claim ownership over independently acquired bytes.

## Decision 5: Add a separate session-integration subsystem and Codex adapter

**Decision**: Add two production projects:

1. `ProgramKit.SessionIntegration` for provider-neutral orchestration,
   canonical definitions, lifecycle evaluation, and adapter contracts; and
2. `ProgramKit.SessionIntegration.Providers.Codex` for the exact first-party
   Codex manifest and skill projection.

Shared public record types and schemas remain in `ProgramKit.Contracts`. The
CLI composes the neutral subsystem and explicitly registers the Codex adapter.
The neutral subsystem may invoke kernel-owned publication and authority
invariants; neither new project is referenced by generated consumer runtime
artifacts.

**Rationale**: The extra project boundary has two independently testable
reasons: development-session code must remain isolated from factory/runtime
code, and provider-specific types must be mechanically absent from canonical
contracts and orchestration. A test-only neutral adapter proves the abstraction
without adding a second supported provider.

**Alternatives considered**:

- Put Codex logic in `ProgramKit.Cli`: rejected because provider mechanics would
  become the canonical public application boundary.
- Put session integration in `ProgramKit.Providers.DotNet`: rejected because an
  AI-session provider is not a .NET factory provider.
- Add one project containing both neutral and Codex code: rejected because
  namespace discipline alone is weak evidence for provider neutrality.
- Add a new kernel-invokable factory provider role: rejected because session
  installation is development-tool lifecycle behavior, not intake mapping,
  construction, or evaluation of consumer software.

## Decision 6: Use a namespaced kernel publication primitive

**Decision**: Generalize the existing kernel publication mechanics into a
namespaced artifact-set publisher. Existing factory construction retains its
current wrapper and paths. Session integration uses a separate state namespace
under `.program-kit/session-integrations/<provider>/` while publishing provider
projections such as `.agents/skills/program-kit/`.

**Rationale**: Installation and removal require the same non-bypassable
candidate sealing, collision preflight, whole-file ownership, durable journal,
post-write digest verification, and receipt-last admission as factory output.
Duplicating those rules in a provider adapter would create a second authority
for trusted workspace mutation. Namespacing prevents the session installation
record and journal from colliding with generated software construction state.

**Alternatives considered**:

- Direct writes from the Codex adapter: rejected because partial output could
  appear trusted and the adapter would own kernel invariants.
- Reuse current publication paths unchanged: rejected because the single
  construction journal and artifact manifest would collide with factory state.
- Transactional in-memory rollback only: rejected because process interruption
  would remain invisible and untrusted bytes could be mistaken for success.

## Decision 7: Model four session lifecycle commands, not a fourth factory role

**Decision**: Extend the public CLI grammar with:

- `program-kit session explain` — read-only candidate and effect explanation;
- `program-kit session install` — authorized publication and admission;
- `program-kit session verify` — read-only current-state evaluation; and
- `program-kit session remove` — separately authorized exact removal.

Each command consumes a versioned request artifact and returns the existing
versioned Program Kit operation-result envelope with a distinct operation
contract identity. These application commands do not extend the closed set of
kernel-invokable factory provider roles.

**Rationale**: The nested grammar makes the conceptual boundary visible while
retaining one CLI and one structured result contract. Separating explanation,
effects, evaluation, and removal prevents dry-run flags, force flags, or
implicit cleanup from acquiring authority.

**Alternatives considered**:

- Reuse top-level factory `construct`: rejected because provider-session
  configuration is not consumer software construction and would blur operation
  roles.
- One `session install --dry-run/--remove/--force`: rejected because mode flags
  make effect and authority semantics ambiguous.
- Provider-specific commands such as `codex install`: rejected because the CLI
  contract must remain provider-neutral.

## Decision 8: Bind effects to exact repository authority artifacts

**Decision**: Effect-bearing session requests must link an exact authority
grant bound to the canonical request digest, workspace identity, operation,
provider, and effect. Read-only explanation and verification require no effect
grant. Installation and removal revalidate the grant immediately before
publication.

Actual human authorship is a `human-review` claim; the repository authority
provider can prove only the exact accepted record and its declared issuer
assurance. The live Codex review record demonstrates that the session asked the
human before the grant appeared. No transcript enters Program Kit results,
locks, receipts, or governed evidence.

**Rationale**: A Boolean `approved` field cannot bind approval to the exact
request or prevent stale reuse. Conversely, local software cannot prove that a
person rather than an agent created a repository record. Separating the
machine-enforced binding from the human-review claim preserves both safety and
semantic honesty.

**Alternatives considered**:

- Treat a chat response as machine-verifiable authority: rejected because the
  CLI cannot authenticate or safely ingest provider transcripts.
- Let the skill grant authority after asking: rejected because instructions
  cannot elevate themselves into a grant.
- Require an external identity service: deferred; it would introduce network,
  credentials, and a new authority provider beyond this local-first proof.

## Decision 9: Use whole-directory ownership for the Codex skill projection

**Decision**: The Codex adapter owns only the exact absent-at-install directory
`.agents/skills/program-kit/`, containing `SKILL.md` and optional
`agents/openai.yaml`. It never edits a shared existing skill, `AGENTS.md`, or
user-level Codex configuration. A collision at that directory fails closed.

**Rationale**: Codex officially discovers repository skills from
`.agents/skills`; a focused skill is the appropriate session capability. A
dedicated directory satisfies whole-file ownership and makes removal exact.
The skill invokes the workspace-local CLI and consumes structured fields; it
contains no domain semantics, planning workflow, approval, or executable
remediation.

**Alternatives considered**:

- Edit `.codex/config.toml`: rejected because a repo skill needs no project
  configuration mutation and shared TOML ownership would be unsafe.
- Edit `AGENTS.md`: rejected because it would mix Program Kit session behavior
  with consumer-owned repository governance.
- Install under user scope: rejected because the first feature explicitly
  supports workspace scope only.
- Bundle scripts inside the skill: rejected because the CLI already owns
  deterministic behavior and duplicate scripts could drift.

## Decision 10: Make provider neutrality a conformance claim, not a slogan

**Decision**: A provider-neutral test adapter consumes the same canonical
definition and emits an in-memory neutral projection. Shared golden scenarios
compare direct CLI, neutral adapter, and Codex projection meaning: operation
identities, effects, authority requirements, result fields, diagnostics, and
dispositions. Provider-specific fields are forbidden in the canonical contract
assembly and schemas.

**Rationale**: One real provider cannot prove neutrality alone. A neutral
harness can prove the contract is independently consumable without declaring a
second provider supported or creating another distribution.

**Alternatives considered**:

- Build a second real provider now: rejected as premature scope before the
  first workflow is usable.
- Assert neutrality through code review only: rejected because the claim has
  mechanically testable aspects.
- Reduce the canonical contract to the intersection of providers: rejected
  because mandatory Program Kit authority and disclosure boundaries cannot be
  weakened for portability.

## Decision 11: Split deterministic automation from live AI evidence

**Decision**: CI will deterministically test package installation, canonical
projection, lifecycle safety, neutral adapter conformance, structured results,
negative paths, runtime isolation, and no-self-host guards on Windows and
Linux. A separate explicitly authorized review script will launch fresh Codex
sessions from an isolated consumer repository for the 10-session behavioral
trials and record only safe outcome classifications and human reviewer
attestation.

The build will not require Codex credentials, a live model, or provider
availability. A missing live review leaves the human/evidence gate pending; it
does not become a fabricated pass or make the repository unable to build.

**Rationale**: Model behavior and provider availability are observations, not
deterministic construction. Running live Codex in Program Kit's mandatory build
would recreate provider coupling and make external state authoritative over the
independent bootstrap.

**Alternatives considered**:

- Run live AI sessions in every CI build: rejected because it adds credentials,
  network dependence, nondeterminism, cost, and provider authority to the
  Program Kit bootstrap.
- Replace live sessions entirely with mocks: rejected because mocks cannot prove
  that an actual session discovers and follows the capability.
- Store full transcripts: rejected by the disclosure boundary and because
  transcripts are not required to prove the bounded outcomes.

## Decision 12: Add a source-authoring marker and fail closed in this repository

**Decision**: Add a versioned Program Kit source-authoring marker at the
repository root. Session installation, verification-as-consumer, and removal
commands detect the marker and return a dedicated blocked diagnostic when the
target is the Program Kit source repository. Packaging and black-box tests use
isolated consumer repositories outside the source tree.

**Rationale**: Documentation alone cannot prevent accidental dogfooding from
becoming a new self-governing dependency. A marker gives the CLI an exact local
invariant while leaving normal build, test, pack, and direct factory contract
tests independent of Program Kit execution.

**Alternatives considered**:

- Detect repository name or remote URL: rejected as ambient, rename-sensitive,
  and forgeable identity.
- Block every repository containing Program Kit source filenames: rejected as
  heuristic and likely to create false positives.
- Permit installation with a force flag: rejected because the independent
  bootstrap boundary is non-waivable in this redesign.

## Decision 13: Keep plugin and marketplace packaging deferred

**Decision**: The Codex projection will be a directly generated repository
skill for this feature. Plugin packaging, marketplace entries, workspace
sharing, and public plugin publication remain future distribution adapters.

**Rationale**: OpenAI documents plugins as installable bundles for skills and
optional MCP servers, but plugin marketplaces introduce separate installation,
cache, enablement, surface, and policy states. The current feature must first
prove that the canonical guidance and CLI behavior are correct. Once proven,
the same Codex projection can be packaged without changing canonical meaning.

**Source**:

- [Package your plugin](https://developers.openai.com/plugins/build/plugins)

**Alternatives considered**:

- Start with a full plugin marketplace: rejected because it tests distribution
  machinery before the session capability itself has passed product review.
- Treat a plugin as provider-neutral: rejected because the plugin manifest and
  installation surface are Codex/ChatGPT-specific projections.

## Decision 14: Extend diagnostics with neutral and Codex namespaces

**Decision**: Reuse existing kernel request, authority, collision, publication,
and external-failure diagnostics where their permanent triggers are unchanged.
Add a neutral session-integration catalog for CLI identity mismatch,
unsupported adapter, stale projection, incompatible provider surface,
invocation-transport failure, and prohibited source workspace. Add a Codex
provider catalog only for Codex-specific skill-discovery, projection, and
fresh-session conditions.

**Rationale**: Reusing a stable ID for a different trigger would corrupt the
public diagnostic contract, while assigning generic failures to the Codex
namespace would make neutral automation provider-dependent. Every new entry
therefore has one permanent invariant and bounded disposition.

**Alternatives considered**:

- Return only prose from setup scripts: rejected because humans and AI sessions
  need stable typed recovery guidance.
- Put all entries in the kernel catalog: rejected because provider-specific
  failures do not belong to kernel authority.
- Treat reload-required as success without qualification: rejected because an
  installed projection is not necessarily available in the current session.
