# Provider adapters

A provider adapter is a thin, provider-specific discovery file that makes one
canonical Program Kit capability visible to one understood AI development
provider. It owns only:

- provider-required trigger and discovery metadata;
- the provider's required output path beneath a human-led workspace root; and
- exact installed-CLI preflight and read commands for one capability ID.

An adapter never copies canonical procedure, authority, safety, or verification
rules. Installing an adapter does not grant authority or begin work.

Initialization is project-scoped only. It rejects the Program Kit source
authoring marker, filesystem roots, and the user-home root so provider-global
`.agents` or `.claude` configuration cannot be written at user-global scope.
Building, packing, and
testing adapter templates never renders a wrapper.

## Implemented provider: Codex

Codex templates live under `provider-adapters/codex/<capability-id>/SKILL.md`.
Each consumer template calls
`program-kit capabilities preflight <capability-id> --workspace-root .` and
`program-kit capabilities read <capability-id> --workspace-root .`. Canonical
knowledge stays embedded in the exact installed CLI. Initialization renders
the templates at `.agents/skills/<capability-id>/SKILL.md`.

The legacy `.codex/skills/` root is not a current adapter contract. Program Kit
recognizes it only as exact ownership-verified migration input during an
explicit human-started initialization or removal operation.

## Implemented provider: Claude Code

Provider identifier: `claude`. Claude Code discovers project-scoped skills at
`.claude/skills/<skill-name>/SKILL.md` beneath the workspace root. Each skill
file carries YAML front matter whose `name` and `description` fields are the
trigger and discovery metadata; the Markdown body is loaded when the skill is
invoked. This local discovery contract was documented from direct provider
behavior of the Claude Code CLI and desktop application (2026 releases, which
also accept the `/<skill-name>` invocation form).

Claude templates live under
`provider-adapters/claude/<capability-id>/SKILL.md` and use the same exact
installed-CLI preflight/read contract as Codex.

The workspace ownership lock at `.program-kit/capabilities.lock.json` records
every initialized reviewed provider plus exact CLI, payload, resource,
template, and output digests. Initializing a second provider preserves the
first provider's verified wrappers. Unowned or modified paths are refused
without partial writes. Explicit
`capabilities uninitialize --provider <claude|codex> --workspace-root <dir>`
removes only one selected exact provider binding and removes the lock only
when no owned provider remains.

Initialization and removal use a durable project-contained journal. An
interrupted operation either already reached the complete desired state or
restores the exact prior bytes on the next explicit lifecycle operation.

Consumer products, not Program Kit, select `none`, `local-optional`, or
`repository-managed` integration. See
[consumer integration postures](../consumer-integration.md) for exact pinned
setup and removal commands and selective Git guidance.

Program Kit source-contributor projections are not consumer wrappers. Their
provider contracts are recorded independently of the consumer CLI provider
allow-list. At a fresh task boundary, the repository refresh operation takes
front matter from the registered adapter template and writes the complete
canonical body into the ignored provider-local capability file. The thin
template body and its canonical-path token are never loaded as contributor
instructions. Source projections are excluded from the installed CLI payload.

## Adding another provider

Another provider is supported only after a human starts provider-adapter work
and the provider's local discovery contract is known from authoritative,
current documentation or direct provider behavior. A contributor must:

1. document the provider identifier, supported version or revision, discovery
   root, file naming rules, trigger metadata, and CLI-retrieval semantics;
2. add inert templates below
   `.agent-capabilities/provider-adapters/<provider>/`;
3. keep each template thin and use exact preflight/read commands rather than
   copying capability rules;
4. register the provider explicitly in the capability source manifest and CLI
   provider allow-list;
5. add positive fixtures for multiple Program Kit locations and negative
   fixtures for missing, substituted, escaping, duplicated, or rule-copying
   adapters;
6. prove deterministic initialization, idempotence, collision refusal,
   ownership-lock updates, and absence of canonical copies in the workspace;
7. update this documentation and package/bundle closure in the same reviewed
   change.

Knowing only an output directory is insufficient. Until the provider's exact
adapter format and discovery behavior are reviewed and tested, Program Kit
must not claim that provider is initialized or supported.

A source-contributor adapter may be registered without adding that provider to
the consumer CLI. Its authoring contract must still record an exact local root,
adapter root, and capability filename; supply reviewed front matter for every
source-contributor capability; and pass the deterministic projection checks.
