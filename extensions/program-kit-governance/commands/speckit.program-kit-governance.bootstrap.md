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
  --input initial_design=./path/to/your-design.md `
  --input integration=codex
```

The example path is illustrative. Always substitute the exact path supplied by the user; do not
assume a filename or search for a conventionally named design file.

If the user explicitly requests one uninterrupted development run with automatic approval and
ratification, append the following workflow input to the command:

```powershell
  --input auto_approve_and_ratify=true
```

Explain that this opts into all three decisions: assessment approval, constitution ratification,
and final bootstrap approval. The workflow still generates and validates every review packet and
records automatic approval provenance so the user can review the complete result afterward.
Never add this input unless the user explicitly requests automatic approval and ratification.

Do not request outside-sandbox or escalated execution, propose an approval exception, create or
install a Codex rule, wrap the command in another shell, or start a new interactive `codex` agent to
run it. A Codex CLI agent is sandboxed too; it is not the normal shell boundary.

If initialization or installation was already run by a Codex agent, warn that rerunning `specify
init` alone may not repair existing ownership or ACLs. Direct the user to
`.specify/extensions/program-kit-governance/references/codex-desktop-windows.md` for the conservative
clean-start procedure.

If preflight reports `PROGRAM_KIT_CONCURRENT_BOOTSTRAP_RUN`, tell the user to verify whether the
listed run still has a live normal-shell `specify workflow` process. Never abandon a live run. If it
is a stale record from a hard-terminated process, display the diagnostic's exact
`codex_bootstrap_preflight.py --abandon-run <run-id>` command for the human to run in the normal
shell. Explain that it preserves the run history while recording an explicit `aborted` terminal
state. Do not run the recovery command from this skill or suggest editing state JSON directly.

After a normal-shell workflow pauses, report the run ID, the concise review-packet path, every
artifact named by that packet, and the exact
`specify workflow resume <run-id> --input <verdict>=<choice>` command. Unless the explicit automatic
option was supplied at startup, the human must run resume from the same normal shell and choose every
verdict themselves. If the human rejects, explain that the run remains paused for revision and that
the packet's documented `write-review --stage ...` command must be run after editing and before
resuming approval. Never describe rejection as approval failure or encourage approving a stale
packet.
