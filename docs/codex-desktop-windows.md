# Windows setup and skill-led founding

Follow the [current installation instructions](https://github.com/orbyss-io/program-kit#install-in-a-repository)
for the supported initializer and normal-shell setup sequence.

Use a normal user-owned PowerShell or WSL terminal for Spec Kit initialization and Program Kit
installation/update. Windows sandbox identities can own generated `.agents` and `.specify` paths;
rerunning init alone does not repair an existing ownership/DACL problem. Preserve work and use the
reviewed clean-start guidance below if affected.

After installation, invoke `$speckit-program-kit-governance-product-intake` inside the current
Codex conversation. It understands the product, authors connected founding artifacts, preserves
provenance and frontier questions, and obtains explicit constitution/ADR review through focused
scripts. It then continues directly to the selected first feature intake. It does not start an
outer workflow or another coding worker. See [focused product founding](../extensions/program-kit-governance/references/product-founding.md).

The former bootstrap workflow is retired. Old run/resume/reopen launchers return an actionable
product-intake diagnostic. Saved workflow records and proof bytes remain historical evidence;
an unfinished run is never marked complete or automatically converted. Upgrade removes only
owned active workflow files/registration and refuses consumer customizations until reconciled.

Interpreter selection and schema dependencies retain their focused setup owners. Prepare the
exact schema runtime only when a validator needs it; missing dependencies remain explicit errors.
Native toolchains, provider accounts and runtime compatibility are checked at the action that
actually requires them, not by founding status. Never copy credentials or loosen sandbox access
as a setup workaround.

## Clean start after agent-owned initialization

Rerunning `specify init` is not an ownership repair. If `.agents`, `.specify`, the repository root,
or files below them are already owned by a sandbox identity, repair ownership and the DACL first or
recreate the working copy under the normal user account.

Before changing anything:

1. Close Codex tasks using the repository.
2. Copy the confirmed intake contract, its bound architecture artifacts, and any other uncommitted work to a safe location
   outside the affected tree.
3. From a normal PowerShell terminal, record `git status`, `git log --oneline`, and
   `git remote -v`.
4. Preserve `.git` unless the human explicitly chooses to discard all repository history.

The conservative option is a clean user-owned working copy:

1. Create a new sibling directory from normal PowerShell or WSL.
2. If the history is available from a remote, clone that remote with `--no-checkout`. If the only
   copy of the history is local, clone the affected repository with `--no-hardlinks --no-checkout`.
   Both approaches preserve Git history while avoiding a checkout of agent-created files.
3. Copy only the backed-up design file and other reviewed uncommitted work into the new working copy.
4. Confirm the new directory, `.git`, and design file are owned by the normal user. Review `git
   status`; do not commit any reported deletions until they are intentional and understood.
5. Run initialization and Program Kit setup from that same normal shell.

If the existing directory must be retained, have the owner or an administrator restore ownership
and appropriate inherited permissions for the repository before removing generated paths. ACL
requirements vary by machine and enterprise policy, so do not apply a blanket `Everyone` grant or
copy an ACL recipe without review. After repair, retain `.git` and the user-selected design file, remove only
the generated content the human has reviewed, and restart setup from the normal shell.

Creating an entirely new Git repository is a separate, destructive choice. Do that only when the
human explicitly decides the old history is unnecessary.

## Do not mask the problem

Do not make `%USERPROFILE%\.codex` writable to a sandbox identity, copy Codex authentication or
state into a repository, globally enable unrestricted agent access, or ask an agent to bypass its sandbox. Those approaches do not correct
agent-owned project paths and blur the intended trust boundary.
