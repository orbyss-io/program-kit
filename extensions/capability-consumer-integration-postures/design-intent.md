# Capability consumer integration posture intent

## Human outcome

Program Kit supplies reviewed provider adapters and deterministic,
project-scoped initialization mechanics. A consumer product owns whether those
mechanics are used and records its decision in the consumer README.

Program Kit documents three supported postures:

1. `none` — the consumer exposes no Program Kit AI-provider integration;
2. `local-optional` — each contributor may explicitly initialize one supported
   provider locally and keep the generated provider binding and ownership
   evidence outside version control;
3. `repository-managed` — the product owner explicitly initializes and commits
   selected provider bindings and ownership evidence for immediate discovery
   after clone.

The posture is consumer documentation and repository policy. It is not runtime
state, package state, an authority grant, or an automatic Program Kit
selection.

## Provider adapter boundary

Program Kit may initialize only adapters whose complete discovery contract,
template, output location, compatibility boundary, tests, and documentation
are reviewed and registered. Recognition of a folder name alone is
insufficient.

Current supported adapters remain finite:

- Codex repository skills use `.agents/skills/<capability-id>/SKILL.md`;
- Claude Code project skills use
  `.claude/skills/<capability-id>/SKILL.md`.

Provider-global roots, user-home configuration, credentials, trust,
permissions, hooks, MCP bindings, and runtime activation remain outside
capability initialization.

## Git and onboarding boundary

Program Kit never changes a consumer `.gitignore`, stages files, commits files,
or infers whether generated files should be shared. Documentation explains
that ignore rules do not suppress already tracked files and recommends
selective tracking of project-scoped adapters rather than committing an entire
provider state directory.

Every consumer README states its selected posture and links to the exact pinned
Program Kit capability-initialization documentation. A link without a
consumer-specific posture statement is insufficient because contributors
could not distinguish intentional absence from incomplete setup.

## Ownership and coexistence

One workspace ownership lock records every Program Kit-owned provider binding,
not only the most recently initialized provider. Initializing one reviewed
provider preserves other exact owned provider bindings. Removing a provider is
an explicit operation that deletes only exact lock-owned wrapper bytes and
updates or removes the lock atomically.

Legacy single-provider locks migrate only during an explicit human-started
initialization or removal. Codex wrappers at the legacy `.codex/skills` path
move to `.agents/skills` only when their current bytes match exact Program Kit
ownership evidence. Modified or unowned files stop migration without partial
mutation.

## Authority and activation

Cloning, package restore, bundle installation, adapter initialization, or
committing generated wrappers does not start work or grant authority. A human
must request the development work, and the active provider loads a thin
wrapper only when its trigger is selected.

No runtime library or generated application reads capability prose or provider
configuration. No startup task, watcher, hook, autonomous loop, or silent
installation is introduced.

## Compatibility and migration

The multi-provider ownership shape is a new lock contract. Legacy lock versions
remain readable only for exact migration. The Codex discovery-root change and
lock-contract change require a new capability-bundle revision and regenerated
consumer bindings.

Capability semantics stay canonical in the verified bundle. Provider wrappers
remain thin relative pointers and contain no copied procedure or authority
rules.

## Acceptance

Acceptance requires deterministic tests for:

- fresh initialization for each supported provider;
- coexistence of Codex and Claude Code bindings;
- idempotent reinitialization;
- exact legacy-lock and legacy-Codex-path migration;
- explicit exact-byte provider removal;
- refusal on tamper, collision, path escape, unsupported provider, incomplete
  bundle, cancellation, and transaction recovery;
- no provider-global, `.gitignore`, Git-index, runtime, or unrelated-file
  mutation;
- exact capability bundle, canonical definition, adapter template, and
  ownership-lock digests;
- clean-clone repository-managed discovery and local-optional guidance.

The existing private Program Kit C# gate remains selected only for
Program Kit-owned implementation. Provider discovery, filesystem ownership,
Git posture, and clean-session behavior remain executable-test and human-review
obligations.
