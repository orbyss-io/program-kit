# Program Kit setup boundary for Codex on Windows

Run `specify init`, Program Kit bundle or extension installation and updates, and
`specify workflow run program-kit-bootstrap ...` yourself from a normal user-owned PowerShell or WSL
terminal. Do not run them from a Codex Desktop task or an interactive Codex CLI agent.

## Reason

OpenAI documents that native Windows agent mode is sandboxed and that its preferred elevated mode
uses dedicated lower-privilege users plus filesystem permission boundaries. OpenAI also documents
that Codex under WSL runs inside the Linux environment. See
[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox) and
[WSL](https://learn.chatgpt.com/docs/windows/wsl).

Program Kit has observed that initialization performed by the dedicated Windows sandbox identity
can leave `.agents`, `.specify`, and related paths owned by that identity. A later elevated-sandbox
refresh may fail to establish protective ACLs, including with `SetNamedSecurityInfoW ... error 5`.
Separately, Spec Kit dispatches Codex workflow commands through `codex exec`, so starting the outer
workflow from an existing Codex agent creates unsupported nested agent execution.

An interactive `codex` CLI agent is also sandboxed; it is not a substitute for a normal shell.

## Safe workflow

1. Open PowerShell directly, or WSL when the repository lives in WSL.
2. Change to the repository root.
3. Run Spec Kit initialization and Program Kit installation or update.
4. Start the outer workflow yourself:

   ```powershell
   specify workflow run program-kit-bootstrap `
     --input initial_design=./INITIAL_DESIGN.md `
     --input integration=codex
   ```

5. Let Spec Kit launch the sandboxed `codex exec` workers.
6. Review every generated artifact and run each `specify workflow resume ...` from the same normal
   shell. The human supplies every verdict.
7. Use Codex Desktop for ordinary repository work afterward.

When the bootstrap skill is invoked from Codex, it must only display the complete command. It must
not execute it, request an exception, create an approval rule, or start another Codex agent.

## Existing affected repository

Rerunning `specify init` alone does not repair ownership. Close Codex, back up `INITIAL_DESIGN.md`
outside the repository, and inspect `git status`, `git log --oneline`, and `git remote -v` from a
normal shell.

Prefer a new user-owned working copy while preserving history:

- Clone the remote with `--no-checkout`, or use `git clone --no-hardlinks --no-checkout` from the
  affected local repository when it contains history not available remotely.
- Copy only the backed-up `INITIAL_DESIGN.md` into the new working copy.
- Confirm the normal user owns the new directory and `.git`, and review `git status` before any
  commit.
- Run initialization and Program Kit setup from that normal shell.

If the existing directory must remain, ask its owner or an administrator to restore correct
ownership and inherited DACLs before removing reviewed generated content. Do not grant `Everyone`
write access. Preserve `.git` unless the human explicitly chooses a completely new repository.
