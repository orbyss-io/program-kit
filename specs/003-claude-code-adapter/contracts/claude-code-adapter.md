# Provider Contract: Claude Code Project-Skill Adapter

## Contract identity

| Subject | Exact initial identity |
|---|---|
| Provider | `anthropic:session-provider:claude-code@2.1.220` |
| Provider surface | `anthropic:provider-surface:project-skill@2.1.220` |
| Adapter | `orbyss.program-kit:session-adapter:claude-code@1.0.0` |
| Canonical definition | Feature 002 `program-kit.session-integration-definition/v1` accepted identity |
| Binding kind | `shell-cli` |
| Scope | `workspace` |

These identities are exact selections. Installed or authenticated Claude Code,
an existing project skill, or a Program Kit executable on `PATH` selects none of
them ambiently.

## Reused public lifecycle

Feature 003 adds no CLI command or factory provider role. It uses Feature 002's
provider-neutral application operations unchanged:

```text
program-kit session explain --workspace <path> --request <path> --format json
program-kit session install --workspace <path> --request <path> --format json
program-kit session verify  --workspace <path> --request <path> --format json
program-kit session remove  --workspace <path> --request <path> --format json
```

The exact Claude adapter is selected in the request. Help and version output add
the adapter/catalog identities but do not change grammar, authority, effect, or
exit-code meaning.

## Provider projection root

```text
.claude/skills/program-kit/
└── SKILL.md
```

The adapter owns the `program-kit` directory only when it was absent before
installation or exact prior admission proves the same owner and bytes. Parent
directories remain consumer-owned containers.

The adapter never writes or modifies:

- `CLAUDE.md` or `CLAUDE.local.md`;
- `.claude/settings.json` or `.claude/settings.local.json`;
- `.claude/commands/`, `.claude/agents/`, hooks, output styles, or plugins;
- `.mcp.json` or any MCP configuration;
- personal, managed, machine-global, or organization configuration;
- provider installation, update channel, credentials, account, model, or
  workspace-trust state; or
- another provider's session projection.

## Exact `SKILL.md`

The file uses UTF-8 without a byte-order mark and LF line endings. Its front
matter contains only:

```yaml
---
name: program-kit
description: Use Program Kit to explain, construct, and evaluate contract-bounded software when the user asks to design or build software through Program Kit or needs help resolving Program Kit diagnostics.
---
```

The initial projection deliberately omits:

- `allowed-tools` and `disallowed-tools`;
- `disable-model-invocation` and `user-invocable` overrides;
- `context`, `agent`, `model`, or dynamic command substitution;
- arguments that can become authority;
- scripts or supporting executable files; and
- copied schemas, manifests, receipts, or consumer semantics.

The body is a concise projection of canonical guidance. It MUST direct Claude
Code to:

1. resolve the repository root and exact workspace-local Program Kit executable
   from the admitted installation record, never global `PATH` selection;
2. verify the CLI version/identity before the first factory operation;
3. use `explain` when meaning, resolution, compatibility, or authority is
   incomplete;
4. consume JSON fields and diagnostic identities as authoritative;
5. ask the human only for bounded missing meaning or approval indicated by the
   result;
6. never create, approve, widen, refresh, or reuse an authority grant;
7. invoke `construct` only with a current exact request-bound grant;
8. use `evaluate` as read-only assessment and never silently repair drift;
9. treat remediation as a proposal requiring a separate request and grant;
10. preserve consumer-owned/custom implementation and report actual effects;
11. stop on unsupported, ambiguous, incompatible, indeterminate, unsafe, or
    unavailable outcomes according to typed dispositions; and
12. avoid Program Kit source inspection, Spec Kit dependence, provider
    transcripts, hidden planning, plugin/MCP invention, and runtime coupling.

## Invocation binding

The adapter normalizes a provider invocation to an executable plus argument
array. It never builds a shell command string from user input or diagnostic
prose.

Factory invocation:

```text
<exact-workspace-program-kit> <operation> --workspace <workspace> --request <request> --format json
```

Session lifecycle invocation:

```text
<exact-workspace-program-kit> session <operation> --workspace <workspace> --request <request> --format json
```

Claude Code's Bash permission and Program Kit effect authority are separate:

- provider permission may allow the process to start;
- Program Kit still requires a current exact grant before any committed effect;
- denial by either boundary prevents the effect; and
- provider permission is never recorded as Program Kit authority.

## Discovery and availability

The adapter can prove the exact file exists at Claude Code's documented project
skill location. It cannot prove an already-running session loaded it.

Verification reports generic installation state separately from provider
availability:

- `not-evaluated` when no live provider observation exists;
- `reload-required` when exact bytes were added after the session began or the
  skill root was not watched at startup;
- `available` only after an exact supported fresh session observes/invokes it;
  and
- `unavailable` when provider version, workspace trust, discovery, or invocation
  prevents use despite intact files.

Provider-specific reasons use the Claude diagnostic catalog. They do not invent
new generic installation states.

## Removal

Removal uses Feature 002's exact admitted record and separate request-bound
grant. It removes only unchanged adapter-owned skill bytes. It preserves parent
directories, Program Kit CLI, Claude Code, settings, credentials, other skills,
other adapters, and every missing, drifted, adopted, or unproven artifact.

## Deferred surfaces

Plugins, marketplaces, MCP, hooks, Claude Desktop, cloud/Cowork behavior, the
Anthropic API, Agent SDK embedding, user skills, and organization-managed skills
are distinct future adapters or distribution profiles. This contract makes no
compatibility claim for them.
