# Program Kit bootstrap from Windows and Codex

Program Kit 0.4.3 requires the human to start repository initialization, Program Kit installation
or update, and outer workflow orchestration from a normal user-owned PowerShell or WSL shell. Do not
ask a Codex Desktop task or an interactive Codex CLI agent to perform those operations.

## Why this boundary exists

Official OpenAI documentation says native Windows agent mode runs in a sandbox. The preferred
`elevated` implementation uses dedicated lower-privilege sandbox users and filesystem permission
boundaries; WSL runs Codex inside its Linux environment instead. See the official
[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox) and
[WSL](https://learn.chatgpt.com/docs/windows/wsl) documentation.

Program Kit's consumer investigation found two independent problems when a Codex agent starts the
outer Spec Kit lifecycle:

1. `specify init` and bundle or extension setup can create `.agents`, `.specify`, and related paths
   as the dedicated Windows sandbox identity. On later turns, the native elevated sandbox may be
   unable to replace those paths' protective ACLs because the invoking Windows user is not their
   owner. The visible failure can include `SetNamedSecurityInfoW ... error 5` and
   `setup refresh had errors`.
2. Spec Kit's Codex integration dispatches workflow command steps by starting `codex exec`. Starting
   `specify workflow run program-kit-bootstrap` from an existing Desktop or CLI agent therefore asks
   a sandboxed agent to start another Codex worker.

Starting an interactive `codex` CLI agent and asking that agent to orchestrate setup is not a normal
shell alternative. The CLI agent is sandboxed too.

## Supported sequence

Use a normal terminal owned by the human account:

1. Open PowerShell directly, or open a WSL shell when the repository and toolchain live in WSL.
2. Change to the repository root.
3. Run `specify init`, catalog registration, and Program Kit installation or update there.
4. Run `specify workflow run program-kit-bootstrap ...` there.
5. Let Spec Kit launch its `codex exec` workflow workers. Those workers remain sandboxed.
6. Run each human-reviewed `specify workflow resume ...` command from the same normal shell.
7. Use Codex Desktop afterward for ordinary repository work and the installed skills.

Example outer command:

```powershell
specify workflow run program-kit-bootstrap `
  --input initial_design=./INITIAL_DESIGN.md `
  --input integration=codex
```

If the installed bootstrap skill is invoked inside Codex, it only formats this command and tells the
user where to run it. It must not execute the command, request an agent exception, or create a
persistent approval rule.

## Clean start after agent-owned initialization

Rerunning `specify init` is not an ownership repair. If `.agents`, `.specify`, the repository root,
or files below them are already owned by a sandbox identity, repair ownership and the DACL first or
recreate the working copy under the normal user account.

Before changing anything:

1. Close Codex tasks using the repository.
2. Copy `INITIAL_DESIGN.md` to a safe location outside the affected tree.
3. From a normal PowerShell terminal, record `git status`, `git log --oneline`, and
   `git remote -v`.
4. Preserve `.git` unless the human explicitly chooses to discard all repository history.

The conservative option is a clean user-owned working copy:

1. Create a new sibling directory from normal PowerShell or WSL.
2. If the history is available from a remote, clone that remote with `--no-checkout`. If the only
   copy of the history is local, clone the affected repository with `--no-hardlinks --no-checkout`.
   Both approaches preserve Git history while avoiding a checkout of agent-created files.
3. Copy only the backed-up `INITIAL_DESIGN.md` into the new working copy.
4. Confirm the new directory, `.git`, and design file are owned by the normal user. Review `git
   status`; do not commit any reported deletions until they are intentional and understood.
5. Run initialization and Program Kit setup from that same normal shell.

If the existing directory must be retained, have the owner or an administrator restore ownership
and appropriate inherited permissions for the repository before removing generated paths. ACL
requirements vary by machine and enterprise policy, so do not apply a blanket `Everyone` grant or
copy an ACL recipe without review. After repair, retain `.git` and `INITIAL_DESIGN.md`, remove only
the generated content the human has reviewed, and restart setup from the normal shell.

Creating an entirely new Git repository is a separate, destructive choice. Do that only when the
human explicitly decides the old history is unnecessary.

## Do not mask the problem

Do not make `%USERPROFILE%\.codex` writable to a sandbox identity, copy Codex authentication or
state into a repository, globally enable unrestricted agent access, add a rule allowing the outer
workflow, or ask an agent to execute it outside its sandbox. Those approaches do not correct
agent-owned project paths and blur the intended trust boundary.
