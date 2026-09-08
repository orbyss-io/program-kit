# Releasing Program Kit 0.10.0

This release splits reusable technical building blocks out of Program Kit while advancing the AI
extensions, governance, generators, preset, and workflow to `0.10.0`. Orbyss Foundation is pinned at
`0.1.0`; Orbyss Forms and Orbyss Localization are pinned independently at `0.1.1`. Program Kit no
longer owns or publishes their runtime artifacts.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Run this complete suite from a normal user-owned terminal only after the user has decided the
candidate should proceed toward publication. It includes the source validators, Chromium/WebKit,
release build, packaged-install checks, previous-release upgrade, disposable local installation, and
the read-only public component-package gate. It writes
`artifacts/release-validation-0.10.0.log` for later inspection and does not run the optional paid
Codex-worker suite.

Before the Program Kit stable tag, verify the already-published component releases and public package
propagation: `dotnet-foundation` `v0.1.0`, `forms` `v0.1.1`, and `localization` `v0.1.1`.

Only after all three replacement families and the 12 Forms npm packages are public and verified
should Program Kit `v0.10.0` be tagged. Legacy `ProgramKit.*` retirement remains a separate, local,
explicitly confirmed operation after all 50 replacement NuGet packages are public and the Program Kit
release workflow has validated public installation and upgrade.

The clean-consumer acceptance must generate 1.1 intake/map artifacts, review the current draft,
confirm explicitly, and validate in that order. The pricing semantic regression must preserve six
journeys, the four evidence-backed candidate contexts, managed Forms versus consumer semantics, all
typed bridges, and founding decision alternatives. The architecture approval regression must
promote only the reviewed founding ADR bundle.

When explicitly authorized, validate the generated DSL with the exact pinned Structurizr Docker
image and visually inspect the localhost diagrams. Keep Firefox in CI; use Chromium and WebKit for
local browser gates per the repository host limitation.

Create and push the stable tag only from the fully validated and explicitly approved release commit:

```powershell
git tag v0.10.0
git push origin main v0.10.0
```

The complete ordered Release workflow must succeed before consumers are told to install. If the
candidate fails, follow the repository's failed stable-release recovery procedure for the same tag.
