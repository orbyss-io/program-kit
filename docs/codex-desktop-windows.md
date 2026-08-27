# Codex Desktop on native Windows

Program Kit 0.4.1 works around a structural execution boundary between Spec Kit 1.0.1 and Codex Desktop's native Windows elevated sandbox.

## Root cause and chosen architecture

Spec Kit's Codex integration dispatches each workflow command step with a new `codex exec` process. When a Codex Desktop task starts the outer `specify workflow run program-kit-bootstrap` inside its elevated sandbox, the nested CLI runs as the dedicated sandbox user. That identity intentionally cannot use the outer user's Codex home, SQLite state, or app-server infrastructure. `--ephemeral` does not bypass initialization, and redirecting SQLite alone does not provide the app-server access the nested CLI also needs.

The official Codex App Server and SDK create or host Codex runs; Spec Kit 1.0.1 has no supported adapter that attaches its command steps to the already-running Desktop task. Program Kit therefore uses the narrowest supported boundary:

- the installed bootstrap skill requests outside-sandbox execution for the outer trusted Program Kit command before trying it;
- the workflow runs a first-step diagnostic and stops before agent dispatch if someone bypasses the skill inside the elevated sandbox;
- an ordinary PowerShell terminal is the fallback;
- the nested Codex CLI then uses its normal state and enforces its own configured sandbox.

Official background: [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox), [agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security), [Codex rules](https://learn.chatgpt.com/docs/agent-configuration/rules), and [Codex App Server](https://learn.chatgpt.com/docs/app-server).

## One-time setup

1. Keep the preferred native Windows elevated sandbox enabled.
2. Ask Codex to use `speckit-program-kit-governance-bootstrap`, passing the initial-design path.
3. Approve outside-sandbox execution only when the command begins with the exact four argument tokens `specify workflow run program-kit-bootstrap`.
4. Optionally choose **Always allow** for only that prefix.
5. If you manually copy `.specify/extensions/program-kit-governance/templates/codex/program-kit-bootstrap.rules` into `%USERPROFILE%\.codex\rules\`, review it first and restart Codex afterward. Program Kit does not install it.
6. Review every generated artifact and explicitly resume the assessment, constitution, and bootstrap gates. The allow rule does not match `specify workflow resume`.

Test a manually installed rule:

```powershell
codex execpolicy check --pretty `
  --rules "$env:USERPROFILE\.codex\rules\program-kit-bootstrap.rules" `
  -- specify workflow run program-kit-bootstrap --input initial_design=./INITIAL_DESIGN.md
```

## PowerShell fallback

```powershell
Set-Location C:\path\to\your\repository
specify workflow run program-kit-bootstrap `
  --input initial_design=./INITIAL_DESIGN.md `
  --input integration=codex
```

## Updating an existing consuming repository

After 0.4.1 is released, run these commands consecutively from the consuming repository. Spec Kit 1.0.1 requires the workflow-first order:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
```

Do not run bootstrap between those commands. Start a new Codex task afterward so it discovers the newly installed bootstrap skill. If the repository is initialized with another integration, replace `codex` in the bundle update command with that integration.

## Do not weaken the boundary

Do not make `%USERPROFILE%\.codex` writable to the sandbox, copy Codex authentication or state into the repository, globally enable `danger-full-access`, switch every user to the unelevated sandbox, or allow `specify workflow` as a broad command prefix.
