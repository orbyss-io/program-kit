# Program Kit Spec Kit Maintenance

Program Kit uses upstream Spec Kit as a managed engine and keeps project policy
in separate, repository-owned layers. Do not edit files named by
`.specify/integrations/*.manifest.json` directly.

## Ownership boundary

| Layer | Location | Upgrade behavior |
|-------|----------|------------------|
| Upstream managed core | `.agents/skills/speckit-*`, `.specify/scripts/`, `.specify/templates/*.md` | Replaced only by manifest-aware Spec Kit upgrade |
| Project artifact shapes | `.specify/templates/overrides/` | Runtime priority over core; not part of upstream manifests |
| Project lifecycle | `.specify/workflows/overlays/speckit/` | Composed over the installed workflow and preserved across workflow refreshes |
| Project constitution | `.specify/memory/constitution.md` | Live project authority; preserved by integration upgrade |
| Project enforcement | `eng/Assert-SpecKitIntegrity.ps1`, `eng/Invoke-Verification.ps1` | Repository-owned and exercised locally and in CI |

Extensions add capabilities and hooks. Presets customize core commands and
templates. Workflow overlays change installed workflow steps. This repository
currently needs template overrides and a workflow overlay; it does not install
an extension merely to imitate functionality those narrower mechanisms already
provide.

## Safe upgrade

1. Create a dedicated branch with a clean worktree.
2. Run `./eng/Invoke-SpecKitUpgrade.ps1` to inspect integration status.
3. Run `./eng/Invoke-SpecKitUpgrade.ps1 -Mode Upgrade`.
4. Never add `--force` to the normal upgrade. A conflict is a review request,
   not permission to discard either upstream or project behavior.
5. Review every changed managed file and manifest.
6. Run `./eng/Invoke-Verification.ps1 -Mode PrePr` and let protected CI provide
   the final Windows/Linux acceptance and evidence proof.

The integrity assertion checks both directions: upstream-managed files must
still match their install manifests, and all project-owned overrides, workflow
anchors, constitutional rules, and verification entry points must still exist.
An incompatible upstream rename or overwrite therefore fails locally and in CI
instead of silently reverting Program Kit to the generic workflow.

The broad `specify init --here --force` path is recovery-only. If it is ever
unavoidable, use a clean branch, inspect the complete diff, and run the same
integrity and pre-PR checks before merging.
