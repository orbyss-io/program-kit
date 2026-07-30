# Contributing to Program Kit

This file describes how to set up a **contributor** workspace: a clone of this
repository in which you work *on* Program Kit's own source. It is different from
a **consumer** workspace, where you build your own software *with* Program Kit
and follow [`README.md`](README.md) instead.

If you are an AI agent helping a human set up this workspace, read the whole
file before running anything.

## How to tell you are in a contributor workspace

This repository is a source **authoring workspace**. It carries the marker
file:

```
.agent-capabilities/authoring-workspace.json
```

While that marker is present, the consumer capability commands
(`capabilities initialize`, `capabilities read`, `capabilities catalog`, and
`dotnet materialize-console-inputs`) **fail closed by design**. That is not a
misconfiguration — it keeps capability source authoring, building, packing, and
fixture verification inert. Do not try to "fix" it by removing the marker or by
installing consumer wrappers.

Detection rule (for humans and agents): if
`.agent-capabilities/authoring-workspace.json` exists, you are a contributor —
use this file. If it does not exist, you are a consumer — use `README.md`.

## Prerequisites

- Git.
- The exact .NET SDK selected by [`global.json`](global.json). Do not use an
  ambient or newer SDK; `rollForward` is disabled on purpose.
- Docker only if you run an explicitly selected container-backed integration
  proof.

## 1. Get the source

Any local folder that holds a clone of this Git repository works — there is no
required parent path, and this repository has no submodules of its own.

```powershell
git clone https://github.com/orbyss-io/program-kit.git
cd program-kit
```

An existing clone you already have is equally valid; just make sure it is on the
commit you intend to work from.

## 2. Build and test

```powershell
dotnet restore ProgramKit.sln --configfile NuGet.Config --locked-mode
dotnet build ProgramKit.sln -c Release --no-restore
dotnet test ProgramKit.sln -c Release --no-build --no-restore
```

## 3. Capabilities in a contributor workspace

There is **no CLI installation or `capabilities initialize` step for
contributors.** The installed consumer CLI deliberately excludes contributor
capabilities and refuses to run against this authoring workspace.

The only capability meant to be active here is the contributor-only
`author-and-maintain-skills`. Its canonical, provider-neutral definition lives
at:

```
.agent-capabilities/capabilities/author-and-maintain-skills/CAPABILITY.md
```

That file is the source of truth. The provider adapters under
`.agent-capabilities/provider-adapters/<provider>/…` are thin registration
wrappers that only point back to it. Because there is no CLI to render them in
this workspace, you wire the wrapper into your agent by hand, per provider, as
described next.

## 4. Wire the contributor capability into your agent (per provider)

Rendering means: copy the repo-frozen adapter template into your provider's
skill discovery root and replace the `{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}`
token with the repository-relative canonical path. Render **only** the provider
your agent actually uses. The rendered file is local workspace state (see
[`.gitignore`](.gitignore)); it is not committed.

### Claude Code

Claude Code discovers project-scoped skills at
`.claude/skills/<name>/SKILL.md` beneath the workspace root.

```powershell
$cap = 'author-and-maintain-skills'
$canonical = ".agent-capabilities/capabilities/$cap/CAPABILITY.md"
$src = ".agent-capabilities/provider-adapters/claude/$cap/SKILL.md"
$dst = ".claude/skills/$cap/SKILL.md"
New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
$body = (Get-Content -Raw $src).Replace('{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}', $canonical)
[System.IO.File]::WriteAllText((Resolve-Path -LiteralPath (Split-Path $dst)).Path + "\SKILL.md", $body, (New-Object System.Text.UTF8Encoding $false))
```

### Codex

Codex discovers project-scoped skills at `.codex/skills/<name>/SKILL.md`.

```powershell
$cap = 'author-and-maintain-skills'
$canonical = ".agent-capabilities/capabilities/$cap/CAPABILITY.md"
$src = ".agent-capabilities/provider-adapters/codex/$cap/SKILL.md"
$dst = ".codex/skills/$cap/SKILL.md"
New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
$body = (Get-Content -Raw $src).Replace('{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}', $canonical)
[System.IO.File]::WriteAllText((Resolve-Path -LiteralPath (Split-Path $dst)).Path + "\SKILL.md", $body, (New-Object System.Text.UTF8Encoding $false))
```

POSIX shell equivalent (either provider — set `provider`):

```bash
provider=claude   # or: codex
cap=author-and-maintain-skills
canonical=".agent-capabilities/capabilities/$cap/CAPABILITY.md"
mkdir -p ".$provider/skills/$cap"
sed "s|{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}|$canonical|g" \
  ".agent-capabilities/provider-adapters/$provider/$cap/SKILL.md" \
  > ".$provider/skills/$cap/SKILL.md"
```

## 5. Verify the wiring

- The rendered file exists at `.<provider>/skills/author-and-maintain-skills/SKILL.md`.
- Its body no longer contains the literal `{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}`
  token; it names the on-disk canonical path instead.
- Its YAML front matter (`name`, `description`) is unchanged from the template.
- In Claude Code, `/author-and-maintain-skills` resolves; the skill loads and
  follows the canonical `CAPABILITY.md`.

## 6. What not to do in a contributor workspace

- Do not run `program-kit capabilities initialize` / `read` / `catalog` here —
  they fail closed against the authoring marker on purpose.
- Do not remove or edit `.agent-capabilities/authoring-workspace.json` to make
  consumer commands run.
- Do not treat a rendered `.claude` / `.codex` skill as the source of the rules.
  The rules live only in the canonical `CAPABILITY.md`; the wrapper just
  registers and loads it.
- Do not hand-edit rendered wrappers; re-render them from the adapter template
  instead.

## Day-to-day authoring

- [`AGENTS.md`](AGENTS.md) — agent startup expectations for this repository.
- [`.agent-capabilities/README.md`](.agent-capabilities/README.md) and
  [`.agent-capabilities/provider-adapters/README.md`](.agent-capabilities/provider-adapters/README.md)
  — the canonical capability tree and adapter contract.
- [`.agent-capabilities/capabilities/INDEX.md`](.agent-capabilities/capabilities/INDEX.md)
  — the authoring capability catalog. Regenerate it with
  `program-kit capabilities render-catalog .agent-capabilities/capabilities/INDEX.md --output <file>`
  (an authoring-only projection; not the consumer readiness catalog).
- [`governance/`](governance) — the C# source quality gate and version-intent
  rules your change must satisfy.
