# Consumer integration postures

Program Kit capabilities are development-session guidance, not application
runtime dependencies. A consumer product owns whether and how those
capabilities are exposed. Program Kit does not infer that choice from folders,
dependencies, or the presence of a Program Kit checkout.

Every consumer README should state one posture and link to this file at the
exact Program Kit revision pinned by that consumer:

- `none`: the product exposes no Program Kit provider integration. No provider
  wrappers or capability ownership lock are expected.
- `local-optional`: a contributor may initialize a supported provider in their
  own checkout. The contributor and product owner decide how the generated
  project files remain untracked.
- `repository-managed`: the product owner initializes, reviews, and commits
  selected provider wrappers, the complete ownership lock, and the exact
  capability bundle. A fresh clone can then expose the selected capabilities
  to a compatible provider without rerunning initialization.

A bare link to Program Kit is not a posture statement. State the selected
posture so contributors can distinguish intentional absence from incomplete
setup.

## Reviewed providers

Bundle `4.0.0` supports only these reviewed project-scoped adapters:

| Provider ID | Current project discovery root |
| --- | --- |
| `codex` | `.agents/skills/<capability-id>/SKILL.md` |
| `claude` | `.claude/skills/<capability-id>/SKILL.md` |

The legacy Codex root `.codex/skills/` is accepted only as exact
ownership-verified migration input. Program Kit does not initialize
user-global provider roots.

Each provider application remains a local prerequisite for the contributor
who wants to use it. Program Kit does not install Codex, Claude Code, a global
CLI, trust, or permissions. Committed wrappers are inert until a compatible
provider discovers them and a human requests work.

## Pinned setup

The commands below assume the consumer pins:

- the Program Kit source checkout at `.\program-kit`; and
- the verified extracted CapabilityBundle `4.0.0` payload at
  `.\.program-kit\capability-bundle\4.0.0\contentFiles\any\any`.

Initialize Codex from the consumer root:

```powershell
dotnet run `
  --project .\program-kit\src\Orbyss.ProgramKit.CommandLine `
  -- `
  capabilities initialize `
  --provider codex `
  --workspace-root . `
  --program-kit-root .\.program-kit\capability-bundle\4.0.0\contentFiles\any\any
```

Initialize Claude Code by changing only the provider:

```powershell
dotnet run `
  --project .\program-kit\src\Orbyss.ProgramKit.CommandLine `
  -- `
  capabilities initialize `
  --provider claude `
  --workspace-root . `
  --program-kit-root .\.program-kit\capability-bundle\4.0.0\contentFiles\any\any
```

Initialization verifies the exact bundle, adds or updates only the selected
provider, preserves every other exact provider binding, and writes lock
version `2.0.0` to `.program-kit/capabilities.lock.json`. Re-run it after an
explicit bundle or Program Kit pin change. Modified, incomplete, colliding, or
ambiguous ownership state fails closed.

If the `program-kit` .NET tool is already installed at a version selected by
the product owner, the equivalent command starts with
`program-kit capabilities initialize`; all arguments remain the same.

## Exact removal

Remove one selected exact Program Kit-owned provider binding:

```powershell
dotnet run `
  --project .\program-kit\src\Orbyss.ProgramKit.CommandLine `
  -- `
  capabilities uninitialize `
  --provider codex `
  --workspace-root .
```

Use `--provider claude` for Claude Code. Removal verifies every selected
wrapper against the ownership lock, preserves all other providers, and removes
the lock only when no Program Kit-owned binding remains. Modified, missing, or
unowned files stop removal. The command does not change the README posture.

## Git choices remain consumer-owned

For `repository-managed`, the product owner normally reviews and explicitly
tracks:

- the selected provider trees, such as `.agents/skills/` and/or
  `.claude/skills/`;
- `.program-kit/capabilities.lock.json`; and
- the exact pinned capability bundle or another reproducible bundle source.

For `local-optional`, those generated project files normally remain untracked
according to the consumer's documented policy. For `none`, they are absent.

Program Kit never edits `.gitignore`, stages files, commits files, chooses a
posture, or silently prompts contributors to initialize. The consumer README
is the onboarding contract; product owners retain the final tracking policy.

No posture grants development authority. A human must still explicitly start
or request each capability-backed task.
