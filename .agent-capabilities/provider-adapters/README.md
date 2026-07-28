# Provider adapters

A provider adapter is a thin, provider-specific discovery file that makes one
canonical Program Kit capability visible to one understood AI development
provider. It owns only:

- provider-required trigger and discovery metadata;
- the provider's required output path beneath a human-led workspace root; and
- one generated pointer to one canonical definition under the selected
  Program Kit `.agent-capabilities/capabilities/` tree.

An adapter never copies canonical procedure, authority, safety, or verification
rules. Installing an adapter does not grant authority or begin work.

Initialization is project-scoped only. It rejects the Program Kit source
authoring marker, filesystem roots, and the user-home root so provider-global
`.codex` or `.claude` configuration cannot be written. Building, packing, and
testing adapter templates never renders a wrapper.

## Implemented provider: Codex

Codex templates live under `provider-adapters/codex/<capability-id>/SKILL.md`.
Each template contains the exact
`{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}` token once. The Program Kit CLI
replaces it with a forward-slash relative path computed from the generated
workspace `.codex/skills/<capability-id>/SKILL.md` to the selected canonical
definition. This keeps the adapter portable when Program Kit is located at
`program-kit/`, `tools/program-kit/`, or another explicit workspace path.

## Implemented provider: Claude Code

Provider identifier: `claude`. Claude Code discovers project-scoped skills at
`.claude/skills/<skill-name>/SKILL.md` beneath the workspace root. Each skill
file carries YAML front matter whose `name` and `description` fields are the
trigger and discovery metadata; the Markdown body is loaded when the skill is
invoked. This local discovery contract was documented from direct provider
behavior of the Claude Code CLI and desktop application (2026 releases, which
also accept the `/<skill-name>` invocation form).

Claude templates live under
`provider-adapters/claude/<capability-id>/SKILL.md`. Each template contains
the exact `{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}` token once. The Program
Kit CLI replaces it with a forward-slash relative path computed from the
generated workspace `.claude/skills/<capability-id>/SKILL.md` to the selected
canonical definition, exactly as for Codex.

The workspace ownership lock at `.program-kit/capabilities.lock.json` records
one provider: the most recently initialized one. Initializing a second
provider renders that provider's wrappers into its own discovery root and
rewrites the lock; wrappers whose bytes are no longer recorded by the current
lock are treated as human-owned and initialization refuses to overwrite them
when they differ.

## Adding another provider

Another provider is supported only after a human starts provider-adapter work
and the provider's local discovery contract is known from authoritative,
current documentation or direct provider behavior. A contributor must:

1. document the provider identifier, supported version or revision, discovery
   root, file naming rules, trigger metadata, and canonical-pointer semantics;
2. add inert templates below
   `.agent-capabilities/provider-adapters/<provider>/`;
3. keep each template thin and use exactly one canonical-path token rather than
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
adapter format and discovery behavior are reviewed and tested, users may ask
that provider to read a canonical capability directly, but Program Kit must not
claim that provider is initialized or supported.
