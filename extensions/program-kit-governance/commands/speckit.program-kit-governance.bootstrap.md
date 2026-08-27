---
description: Explain the safe normal-shell boundary for Program Kit bootstrap and provide a copyable command.
---

## Input

Treat `$ARGUMENTS` as the initial-design path followed by any explicitly requested Program Kit
workflow inputs. Require an initial-design path. Do not infer a different design file when multiple
candidates exist.

## Required execution boundary

This skill is guidance-only. Never run `specify init`, Program Kit bundle or extension installation
or update commands, or `specify workflow run program-kit-bootstrap` from a Codex Desktop task or an
interactive Codex CLI agent.

Spec Kit dispatches Codex workflow command steps by starting `codex exec`. If a sandboxed Codex
agent starts the outer workflow too, execution becomes nested. On native Windows, initialization or
installation performed by the elevated sandbox's dedicated identity can also leave `.agents`,
`.specify`, and related paths owned by that identity. A later sandbox refresh may then be unable to
establish its protective ACL boundary.

When this skill is invoked:

1. Construct the complete command from the supplied initial-design path and inputs.
2. Display it in a fenced code block for the user to copy.
3. Tell the user to open a normal user-owned PowerShell or WSL terminal in the repository root and
   run the command themselves.
4. Stop. Do not call a shell tool for the command.

The command normally has this form:

```powershell
specify workflow run program-kit-bootstrap `
  --input initial_design=./INITIAL_DESIGN.md `
  --input integration=codex
```

Do not request outside-sandbox or escalated execution, propose an approval exception, create or
install a Codex rule, wrap the command in another shell, or start a new interactive `codex` agent to
run it. A Codex CLI agent is sandboxed too; it is not the normal shell boundary.

If initialization or installation was already run by a Codex agent, warn that rerunning `specify
init` alone may not repair existing ownership or ACLs. Direct the user to
`.specify/extensions/program-kit-governance/references/codex-desktop-windows.md` for the conservative
clean-start procedure.

After a normal-shell workflow pauses, report the run ID, the artifact to review, and the exact
`specify workflow resume <run-id> --input <verdict>=<choice>` command. The human must run resume from
the same normal shell and choose every verdict themselves.
