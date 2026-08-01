# Research: Claude Code Session Adapter

**Feature**: `003-claude-code-adapter`
**Date**: 2026-08-01
**Status**: Complete — no unresolved technical clarifications

## Decision 1: Reuse Feature 002 without redefining it

**Decision**: Feature 003 consumes the provider-neutral session definition,
request, installation record, lifecycle commands, structured result, authority
model, publication mechanics, and neutral conformance harness from Feature 002.
It adds a first-party Claude Code adapter and provider-specific evidence only.

**Rationale**: The purpose of a second provider is to test the existing
abstraction. Changing canonical meaning inside the adapter would evade that
test. Any mandatory requirement that cannot be expressed through Feature 002
must be reported as an upstream contract gap and resolved before this adapter is
implemented.

**Alternatives considered**:

- Extend Feature 002 to support two providers: rejected because Feature 002 is
  deliberately scoped to the first real provider plus a neutral harness.
- Copy the Feature 002 contracts into this feature: rejected because duplicated
  source truth can drift and falsely appear compatible.
- Hide Claude-specific fields in a generic extension bag: rejected because
  untyped provider data would weaken exact conformance.

## Decision 2: Use Claude Code project skills as the projection surface

**Decision**: The adapter projects one repository-scoped skill at
`.claude/skills/program-kit/SKILL.md`. Claude Code's existing Bash capability
invokes the exact workspace-local `program-kit` executable. No dedicated native
tool registration or MCP server is introduced.

**Rationale**: Anthropic documents project skills as the version-controlled,
project-only surface for reusable workflows. Skills are discovered from the
working directory and parent directories to the repository root, including in
fresh interactive and ordinary `claude -p` sessions. This is the smallest
official surface that can project canonical session guidance without editing
global configuration.

**Sources**:

- [Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [Extend Claude Code overview](https://code.claude.com/docs/en/features-overview)

**Alternatives considered**:

- `CLAUDE.md`: rejected because it is always-loaded consumer governance, not a
  separately identifiable on-demand capability.
- `.claude/commands`: rejected because Anthropic now recommends skills and
  treats legacy commands as the older compatibility surface.
- `.claude/settings.json`: rejected because the adapter needs no shared project
  settings and cannot safely claim whole-file ownership.
- A Claude Code plugin: deferred until the direct project skill has passed
  product review; plugin distribution must not redefine canonical meaning.
- MCP: rejected because the local CLI already exposes the required structured
  contract and an extra server lifecycle has no demonstrated need.

## Decision 3: Project a minimal skill with no permission grant

**Decision**: The skill contains `name` and `description` front matter plus a
concise deterministic projection of canonical guidance. It omits
`allowed-tools`, `disallowed-tools`, `context`, dynamic commands, scripts, and
settings. Model invocation remains enabled so Claude can discover the skill for
relevant software-factory intent; effect authority remains exclusively in the
Program Kit request/grant contract.

**Rationale**: Claude Code's `allowed-tools` field can pre-approve tools for the
turn in which a skill is invoked. That is a provider permission feature, not a
Program Kit human effect grant, and including it would create avoidable
authority confusion. Loading guidance or invoking read-only explanation may be
automatic, while Program Kit independently blocks every effect without a
current request-bound grant.

**Source**:

- [Skill invocation and tool permissions](https://code.claude.com/docs/en/slash-commands#control-who-invokes-a-skill)

**Alternatives considered**:

- `disable-model-invocation: true`: rejected for the reference adapter because
  it would prevent the intended natural-language discovery proof. A user can
  still invoke `/program-kit` explicitly.
- Add exact Bash rules to `allowed-tools`: rejected because a projected skill
  should not silently change provider permission behavior.
- Bundle an invocation script: rejected because the CLI owns behavior and a
  second executable projection could drift.

## Decision 4: Claim exact support for Claude Code 2.1.220

**Decision**: The initial compatibility profile targets exactly Claude Code
`2.1.220`, the current official release observed during planning. The target
machine installs that exact release through a separately managed provider
bootstrap, verifies `claude --version`, and records the observed executable
digest. The adapter neither installs nor updates Claude Code.

**Rationale**: Anthropic documents exact-version native installation and exact
version reporting. A single pinned provider release creates a reproducible first
proof; a floating `latest` or `stable` channel would allow provider behavior to
change without adapter or evidence identity changing.

**Sources**:

- [Claude Code v2.1.220 release](https://github.com/anthropics/claude-code/releases/tag/v2.1.220)
- [Install a specific version](https://code.claude.com/docs/en/installation#install-a-specific-version)

**Alternatives considered**:

- Support all `2.1.x` versions: rejected because skill parsing, live reload,
  print-mode behavior, and structured-output semantics changed within that
  family.
- Follow `latest`: rejected because installation time would become an ambient
  compatibility input.
- Have Program Kit disable provider updates: rejected because provider
  installation and settings remain externally owned.

## Decision 5: Keep deterministic conformance separate from live Claude behavior

**Decision**: Deterministic CI validates exact skill bytes, manifest/schema
conformance, lifecycle safety, normalized invocation intent, diagnostics, and
cross-provider semantic parity without launching Claude Code. A separate
authorized isolated-machine review runs exact Claude Code sessions and records
only bounded classifications plus independently observed Program Kit evidence.

**Rationale**: Model behavior, authentication, billing, service availability,
and provider output are external observations. They cannot become deterministic
bootstrap or release claims. The adapter's projection and public contract can
and must remain fully testable offline after exact inputs are available.

**Alternatives considered**:

- Require live Claude Code in CI: rejected because it adds credentials,
  nondeterminism, cost, network, and external availability to Program Kit's
  independent source build.
- Test only with mocks: rejected because mocks cannot establish actual project
  skill discovery or session behavior.
- Store full provider transcripts: rejected by the disclosure boundary and not
  needed for bounded outcome verification.

## Decision 6: Use ordinary print mode for repeatable live trials

**Decision**: Automated live trials use ordinary `claude -p` from the consumer
repository, not `--bare`, because bare mode explicitly skips skill discovery.
The prompt either explicitly invokes `/program-kit` or presents an agreed
natural-language trigger. `--output-format json` plus `--json-schema` constrains
the trial classification, and an exact command-line `--allowedTools` rule may
permit only the workspace-local Program Kit executable for that headless trial.

Raw provider output is parsed transiently and discarded. Program Kit results,
filesystem state, and receipts are independently inspected; Claude's reported
success is never sufficient evidence.

**Rationale**: Anthropic documents that ordinary print mode loads the same
project context as an interactive session, user-invoked skills work in print
mode, and bare mode skips skills. Command-line tool permission is bounded test
harness configuration and does not replace the Program Kit authority grant.

**Source**:

- [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)

**Alternatives considered**:

- `claude --bare -p`: rejected because it would bypass the projection being
  tested.
- Interactive-only trials: rejected because they are difficult to repeat and
  compare, though one interactive walkthrough remains a required human review.
- Trust the provider's final answer: rejected because evidence must bind actual
  Program Kit results and effects.

## Decision 7: Use whole-directory ownership and no shared-file edits

**Decision**: The adapter owns only a previously absent or exactly admitted
`.claude/skills/program-kit/` directory. The first projection contains only
`SKILL.md`. Parent directories are consumer-owned containers. The adapter never
edits `CLAUDE.md`, `.claude/settings.json`, `.claude/settings.local.json`,
`.claude/commands`, plugins, MCP configuration, credentials, or user scope.

**Rationale**: Whole-directory ownership permits atomic publication and exact
removal without merging consumer settings. A collision with any pre-existing
`program-kit` skill fails closed.

**Alternatives considered**:

- Merge into an existing skill: rejected because mixed ownership makes drift
  and removal ambiguous.
- Generate settings permissions: rejected because provider permission policy is
  consumer-owned and unnecessary for interactive use.
- Install a personal skill: rejected because Feature 003 is workspace-scoped.

## Decision 8: Preserve provider trust as a separate observation

**Decision**: Installation can prove only that exact project-skill bytes are in
the documented location. Claude Code workspace trust, skill discovery, current
session loading, and actual invocation remain separate provider observations.
If the project has not been trusted, the adapter reports provider availability
as unavailable or not evaluated with a provider-specific reason; it does not
change trust settings.

**Rationale**: Anthropic requires users to review project skills before trusting
a workspace, particularly because skills may contain tool permissions. Program
Kit cannot grant that trust or infer it from filesystem state.

**Source**:

- [Claude Code permissions](https://code.claude.com/docs/en/permissions)

**Alternatives considered**:

- Treat installation as session availability: rejected because an already
  running or untrusted session may not load the skill.
- Automate workspace trust: rejected because it is a provider-owned human trust
  decision.

## Decision 9: Add one provider project and explicit catalog registration

**Decision**: Add `ProgramKit.SessionIntegration.Providers.ClaudeCode` as a
production project depending on the Feature 002 neutral session subsystem. The
CLI explicitly registers its exact first-party manifest beside the Codex
adapter. Existing factory providers and generated runtime projects cannot
reference it.

**Rationale**: A separate project is mechanically testable evidence that
Claude-specific paths, front matter, provider versions, and diagnostics do not
leak into neutral contracts or the kernel. Explicit catalog registration keeps
installation distinct from activation and selection.

**Alternatives considered**:

- Add Claude logic to the Codex project: rejected because providers have
  different ownership and compatibility identities.
- Add it to the neutral subsystem: rejected because provider vocabulary would
  become canonical.
- Dynamic provider discovery: rejected by the v1 first-party-only boundary.

## Decision 10: Export a sealed isolated-machine review kit

**Decision**: Source-side tooling exports a verification kit containing the
exact Program Kit tool package, consumer fixtures, expected contract identities,
safe review scripts, and a manifest of digests. The external machine receives
that kit, separately installs/authenticates exact Claude Code, creates a clean
consumer repository, and returns only the safe review record and referenced
Program Kit evidence.

**Rationale**: The target machine must not clone Program Kit source or require
Spec Kit, but its proof still needs exact inputs and repeatable instructions. A
sealed handoff distinguishes distribution evidence from source execution and
prevents a reviewer from silently testing different bytes.

**Alternatives considered**:

- Clone Program Kit on the target machine: rejected because it violates the
  independent consumer boundary.
- Download floating artifacts during the test: rejected because external state
  could change after review begins.
- Manually transcribe results: rejected because exact identities and negative
  outcomes would be lost.

## Decision 11: Add only Claude-specific diagnostics

**Decision**: Reuse Feature 002 neutral and kernel diagnostics for identical
request, authority, collision, drift, publication, and removal triggers. Add
`program-kit.session.claude-code/PKCLDxxxx` entries only for exact Claude Code
version support, skill projection, project discovery/trust, invocation
transport, and live-review conditions.

**Rationale**: Neutral failures must remain automatable across providers, while
provider-specific remediation must not contaminate the shared catalog. Each new
ID has one permanent trigger and stable disposition.

**Alternatives considered**:

- Copy Codex diagnostics: rejected because identical wording does not establish
  identical provider behavior.
- Put every failure in the Claude namespace: rejected because it would hide
  shared kernel invariants.

## Decision 12: Defer plugin, hooks, settings, and broader Anthropic surfaces

**Decision**: Feature 003 supports only the Claude Code CLI project-skill
surface. Claude Desktop, Anthropic API/Agent SDK integration, plugins,
marketplaces, hooks, settings mutation, MCP, cloud sessions, and organization-
managed deployment are outside scope.

**Rationale**: These are different provider or distribution surfaces with
distinct authority, lifecycle, and evidence requirements. The project skill is
sufficient to test the provider-neutral Program Kit contract on an isolated
consumer machine.

**Alternatives considered**:

- Treat every Claude surface as compatible: rejected because shared branding is
  not a contract.
- Add a plugin immediately: rejected because packaging should follow, not
  precede, a successful direct capability proof.
