# Codex Desktop on native Windows

## Why bootstrap needs one narrow exception

Spec Kit 1.0.1 implements a Codex workflow command step by starting `codex exec`. When `specify workflow run program-kit-bootstrap` is itself launched by a Codex Desktop task, this creates a nested Codex CLI.

Codex Desktop's preferred native Windows `elevated` sandbox uses dedicated lower-privilege sandbox users and blocks writes outside the workspace. Codex state under the user's protected `.codex` directory is intentionally unavailable to that identity. The nested CLI may therefore report that it cannot find a home directory, cannot write `state_5.sqlite`, or cannot initialize its in-process app-server client. `CODEX_HOME`, `codex exec --ephemeral`, and redirecting only SQLite storage do not remove every state and app-server requirement.

Program Kit cannot attach Spec Kit's workflow steps to the already-running Desktop task. Codex App Server is an interface for products that host their own Codex client, while the Codex SDK starts automated Codex runs; neither is a child-process bridge into the current Desktop task. Until Spec Kit provides an in-process/current-task Codex dispatcher, the supported boundary is to run the outer trusted Program Kit workflow command outside the outer task sandbox. The nested Codex CLI can then use its normal state and apply its own configured sandbox.

## One-time Codex experience

1. Keep `[windows] sandbox = "elevated"` enabled.
2. Ask Codex to use the `speckit-program-kit-governance-bootstrap` skill, or ask it to run the Program Kit bootstrap outside the current task sandbox before the first attempt.
3. Approve only the exact prefix `specify workflow run program-kit-bootstrap`.
4. Optionally select **Always allow** for that exact prefix. Review the proposed prefix before accepting it.
5. If you manually copy the provided `.rules` template to a trusted Codex rules layer such as `%USERPROFILE%\.codex\rules\program-kit-bootstrap.rules`, restart Codex. Program Kit never copies or enables the rule itself.
6. Leave `specify workflow resume` outside the allow rule. Review the displayed assessment, constitution, or bootstrap artifact and explicitly approve each gate.

The shipped rules template contains `match` and `not_match` examples. Validate a copied file with:

```powershell
codex execpolicy check --pretty `
  --rules "$env:USERPROFILE\.codex\rules\program-kit-bootstrap.rules" `
  -- specify workflow run program-kit-bootstrap --input initial_design=./INITIAL_DESIGN.md
```

## Ordinary PowerShell fallback

From the consuming repository root:

```powershell
specify workflow run program-kit-bootstrap `
  --input initial_design=./INITIAL_DESIGN.md `
  --input integration=codex
```

This fallback is also the normal path for people who launch Program Kit directly instead of from a Codex task. WSL, other operating systems, and non-Codex integrations do not require the Windows-specific exception.

## Unsafe non-solutions

Do not make `%USERPROFILE%\.codex` writable to the sandbox, copy Codex authentication or state into a project, globally enable `danger-full-access`, broadly allow `specify workflow`, or weaken every task to the unelevated sandbox.
