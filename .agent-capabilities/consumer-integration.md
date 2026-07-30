# Consumer integration postures

Program Kit capabilities are development-session guidance, not application
runtime dependencies. A consumer product owns whether and how those
capabilities are exposed. Program Kit does not infer that choice from folders,
package dependencies, or the presence of a Program Kit checkout.

Every consumer README should state one posture and link to this file at the
exact Program Kit version or revision pinned by that consumer:

- `none`: the product exposes no Program Kit provider integration. No provider
  wrappers or capability ownership lock are expected.
- `local-optional`: a contributor may install the exact Program Kit CLI and
  explicitly initialize a supported provider in their own checkout. The
  contributor and product owner decide how those project files remain
  untracked.
- `repository-managed`: the product owner initializes, reviews, and commits
  selected provider wrappers and the complete ownership lock. A fresh clone
  exposes the selected thin adapters immediately, while each contributor still
  installs the exact pinned CLI locally so preflight and canonical reads work.

A bare link to Program Kit is not a posture statement. State the selected
posture so contributors can distinguish intentional absence from incomplete
setup.

## Reviewed providers

Program Kit `0.1.0-alpha.3` supports only these reviewed project-scoped
adapters:

| Provider ID | Current project discovery root |
| --- | --- |
| `codex` | `.agents/skills/<capability-id>/SKILL.md` |
| `claude` | `.claude/skills/<capability-id>/SKILL.md` |

The legacy Codex root `.codex/skills/` is accepted only as exact
ownership-verified migration input. Program Kit does not initialize
user-global provider roots.

Each provider application remains a local prerequisite for the contributor
who wants to use it. Program Kit does not install Codex, Claude Code, trust,
credentials, or permissions. Committed wrappers are inert until a compatible
provider discovers them and a human requests work.

## Pinned setup

Install the exact `Orbyss.ProgramKit.CommandLine` `0.1.0-alpha.3` tool from the
consumer's documented Program Kit feed. Do not select an ambient `latest`.
The Program Kit README documents the exact downloadable-feed installation
journey.

From the human-led consumer workspace root, initialize Codex:

```powershell
program-kit capabilities initialize --provider codex --workspace-root .
```

Initialize Claude Code by changing only the provider:

```powershell
program-kit capabilities initialize --provider claude --workspace-root .
```

Initialization verifies the exact knowledge closure embedded in the installed
CLI, adds or updates only reviewed provider bindings, preserves every other
exact provider binding, and writes
`.program-kit/capabilities.lock.json`. Re-run it only after an explicit CLI
version change or to create local-optional state. Modified, incomplete,
colliding, or ambiguous ownership fails closed.

Check readiness without changing the workspace:

```powershell
program-kit capabilities catalog --workspace-root . --format text
program-kit capabilities preflight design-software --workspace-root .
```

The capability bundle version recorded in the lock is the Program Kit package
version, `0.1.0-alpha.3`. The lock-format version is a separate compatibility
contract and is not a package-version claim.

## Exact removal

Remove one selected exact Program Kit-owned provider binding:

```powershell
program-kit capabilities uninitialize --provider codex --workspace-root .
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
- documentation that pins the exact Program Kit CLI acquisition path and
  version.

For `local-optional`, those generated project files normally remain untracked
according to the consumer's documented policy. For `none`, they are absent.

Program Kit never edits `.gitignore`, stages files, commits files, chooses a
posture, or silently prompts contributors to initialize. Ignore rules do not
untrack files that a product owner already committed. Track only the selected
project-scoped adapter files and ownership evidence, not an entire provider
state directory by convention.

No posture grants development authority. A human must still explicitly start
or request each capability-backed task.
