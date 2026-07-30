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

## Branch lifecycle (required)

Program Kit uses short-lived non-default branches. GitHub's
`delete_branch_on_merge` repository setting is enabled so a pull request's head
branch is automatically removed after GitHub merges it into `main`.

After any merge, update `origin/main` and prove the topic-branch tip is
reachable before cleanup:

```powershell
git fetch origin --prune
git merge-base --is-ancestor <topic-branch> origin/main
```

Only a successful ancestry check permits deletion. If a merge path did not
trigger GitHub's automatic cleanup, delete the merged remote branch explicitly,
then delete the clean local branch with `git branch -d`. Remove an associated
worktree only when it is clean and no contributor or agent is using it.

Never delete `main`, a protected branch, an unmerged branch, a dirty branch, or
a branch attached to active work. Do not substitute `git branch -D` for a
failed ancestry check. Preserve the branch and report its unique commits when
its disposition needs a human decision.

## 2. Build and test

```powershell
dotnet restore ProgramKit.sln --configfile NuGet.Config --locked-mode
dotnet build ProgramKit.sln -c Release --no-restore
dotnet test --solution ProgramKit.sln -c Release --no-build --no-restore --minimum-expected-tests 1
```

`global.json` selects Microsoft Testing Platform. Use its explicit
`--solution`, `--project`, or `--test-modules` selector rather than a positional
path. Do not pass the legacy `--maxcpucount` switch to `dotnet test`: under MTP
it can build successfully and then discover zero tests. When a serialized
build is needed, run `dotnet build --maxcpucount:1` first and then run
`dotnet test --no-build`.

## 3. Capabilities in a contributor workspace

There is **no CLI installation, `capabilities initialize`, or capability
reactivation step for contributors.** The installed consumer CLI deliberately
refuses to run capability delivery operations against this authoring
workspace.

Source-contributor skills are ignored provider-local state. The authoring
marker registers each supported contributor-adapter ID, repository-local skill
root, adapter root, and capability filename independently of the consumer CLI
provider allow-list. Each provider-ready skill contains that adapter's front
matter followed by the complete canonical definition; capability loading
never depends on a runtime file-path reference or an installed Program Kit
CLI. The available source-contributor flows are:

- `author-and-maintain-skills`;
- `develop-software`;
- `design-software`;
- `design-csharp-build-gate`;
- `implement-software-plan`; and
- `maintain-software`.

At the beginning of a fresh task, before loading one of these capabilities,
run:

```powershell
pwsh -NoProfile `
  -File build/Sync-SourceContributorCapabilities.ps1 `
  -Provider <active-provider-id> `
  -RefreshIfStale
```

That deterministic operation refreshes only missing or stale local copies. Do
not run it after a capability has been loaded for the active task. Run it again
only in a new task or when the human explicitly asks to try the newly authored
definition. This keeps an in-progress capability edit from changing the rules
under which it is being performed.

The local copies are provider registration, not consumer installation output
or alternate rule sources. They remain ignored and never enter a commit,
package, or consumer ownership lock. Provider discovery still grants no
authority: a human must start every task.

`publish-dotnet-application-locally` remains a consumer CLI operation and is
not registered for Program Kit source contributors.

## 4. Verify contributor registration

- `.agent-capabilities/authoring-workspace.json` records
  `sourceContributorRegistration: provider-local` and
  `sourceContributorRefresh: fresh-session-or-human-request`.
- The selected contributor-adapter ID resolves to exactly one registered local
  root, adapter root, capability filename, and existing adapter template.
- Every local capability file contains the exact complete canonical definition
  after provider front matter.
- The local skills contain no path-only loader in place of the canonical body
  and do not require consumer capability delivery.
- Consumer capability operations continue to reject this authoring workspace.

Repository conformance tests verify the finite refresh contract, canonical and
adapter inputs, ignored local root, and continued consumer-initialization
denial. The refresh command owns exact local body comparison.

## 5. What not to do in a contributor workspace

- Do not run `program-kit capabilities initialize` / `read` / `catalog` here —
  they fail closed against the authoring marker on purpose.
- Do not remove or edit `.agent-capabilities/authoring-workspace.json` to make
  consumer commands run.
- Do not treat a provider-local skill as the source of the rules. The rules
  live only in the canonical `CAPABILITY.md`; the local file is a disposable,
  deterministic provider projection.
- Do not refresh a loaded capability during an active task unless the human
  explicitly requests that experiment.
- Do not commit source-contributor projections, replace them with consumer CLI
  wrappers, invent an unregistered provider contract, or add generated
  consumer ownership state to this repository.

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
