# Provider Contract: Codex Repository-Skill Projection

## Supported surface

The first Codex adapter uses the officially documented installed-CLI plus
companion-skill pattern. It does not register a dedicated native Codex tool and
does not expose an MCP server. Codex invokes the exact workspace-local
`program-kit` executable through its existing shell capability.

The adapter is first-party, explicitly registered in the Program Kit
distribution, and selected by exact identity. Installed or discovered Codex
state never selects it ambiently.

## Projection root

```text
.agents/skills/program-kit/
├── SKILL.md
└── agents/
    └── openai.yaml       # optional UI metadata; no product logic
```

The complete `program-kit` directory must be absent before first installation
or exactly match the admitted installation record. The adapter does not edit:

- `.codex/config.toml`;
- `AGENTS.md`;
- another skill directory;
- user or machine Codex configuration; or
- a plugin marketplace.

Every projected file is whole-file `generated-owned`. The parent `.agents` and
`.agents/skills` directories remain consumer-owned containers.

## `SKILL.md` projection

The skill has exact front matter:

- `name`: `program-kit`;
- `description`: a concise trigger identifying human-led software construction,
  Program Kit explanation, construction, evaluation, and diagnostic recovery;
  and
- no provider selection, authority, model, domain, or version claim in the
  trigger text.

The body is an exact projection of canonical guidance plus Codex-specific
invocation mechanics. It must direct Codex to:

1. resolve the consumer repository root and the exact workspace-local
   executable for the active operating system;
2. call `version --format json` and reject a mismatch before other work;
3. use `explain` whenever intent, resolution, or authority is incomplete;
4. treat JSON fields and diagnostic identities as authoritative and rendered
   text as non-authoritative;
5. ask the human for exact missing meaning or approval indicated by the result;
6. never create, widen, refresh, or reuse an authority grant on its own;
7. invoke `construct` only after a current exact request-bound grant exists;
8. use `evaluate` for read-only current-state assessment;
9. treat remediation as a proposal requiring a separate request and authority;
10. preserve custom implementation and consumer-owned files;
11. stop on unsupported, ambiguous, incompatible, indeterminate, or unsafe
    outcomes according to the typed disposition; and
12. avoid Program Kit source inspection, Spec Kit dependence, hidden planning,
    provider transcripts, and runtime coupling.

The skill contains no script, copied JSON Schema, provider manifest, consumer
domain semantics, executable repair command, or approval statement.

## Optional `agents/openai.yaml`

When present, metadata may define display name, short description, icon paths,
brand color, default prompt, and implicit invocation policy. It must not:

- declare an MCP dependency for this feature;
- contain a CLI version or path that competes with the installation record;
- weaken explicit human invocation or approval behavior;
- introduce additional instructions; or
- become required by the canonical definition.

Failure to preserve these constraints makes the adapter projection invalid.

## Invocation binding

The installed CLI lives under the dedicated workspace-local external tool
directory. The projection uses the exact repository-relative executable path
for Windows or POSIX declared by the installation request. It never searches
global PATH to select a Program Kit version.

Every factory call uses:

```text
<exact-program-kit> <operation> --workspace <workspace> --request <request> --format json
```

Every session lifecycle call uses:

```text
<exact-program-kit> session <operation> --workspace <workspace> --request <request> --format json
```

Arguments are passed as an array through the provider's shell capability. The
skill never constructs a shell-evaluated command string from diagnostic prose
or user-controlled output.

## Discovery and reload

Codex discovers repository skills from `.agents/skills` between the current
working directory and repository root. Artifact installation can therefore
prove only that the exact skill is in the documented discovery location.

Provider-session availability is separate:

- after publication, `sessionAvailability` is `reload-required` or
  `not-evaluated`;
- a fresh real Codex session may establish `available` for the exact observed
  provider version; and
- failure to observe the skill establishes `unavailable` or `not-evaluated`,
  never installation drift unless file evidence also differs.

## Conformance profile

The Codex adapter is supported only when fixtures prove:

- exact projection bytes and canonical-definition binding;
- discovery from repository root and nested working directories;
- Windows and POSIX path and argument preservation;
- clean JSON stdout reaches the session without provider rewriting;
- effect-bearing operations remain recognizable as requiring human authority;
- diagnostic identities and dispositions remain available to the session;
- current-session versus fresh-session state is reported honestly; and
- provider-local material contains no canonical provider-neutral fields beyond
  exact bindings.

The local planning observation used Codex CLI `0.137.0`. That observation is
test evidence, not a floating compatibility promise. Other provider versions
remain `not-evaluated` until the exact adapter conformance suite supports them.

## Future plugin packaging

A future Codex distribution adapter may package this same skill in a plugin and
marketplace. That packaging must retain the canonical definition binding and
must not redefine Program Kit operations, authority, diagnostics, or provider
neutrality. MCP remains a separate future binding kind rather than an implicit
upgrade of this adapter.
