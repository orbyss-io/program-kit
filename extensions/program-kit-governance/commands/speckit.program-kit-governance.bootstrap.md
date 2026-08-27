---
description: Run Program Kit bootstrap safely, including Codex Desktop Windows sandbox escalation before nested Codex dispatch.
---

## Input

Treat `$ARGUMENTS` as the initial-design path followed by any explicitly requested Program Kit workflow inputs. Require an initial-design path. Do not infer a different design file when multiple candidates exist.

## Execution boundary

Program Kit's Spec Kit 1.0.1 workflow dispatches each Codex command step through a new `codex exec` process. On native Windows, that nested process cannot initialize from inside Codex Desktop's elevated sandbox because the sandbox identity has no usable writable Codex home/state or app-server client.

When this skill is running in a Codex Desktop task on native Windows:

1. Do not first attempt the workflow command inside the task sandbox.
2. Construct a direct command whose first four argument tokens are exactly:

   ```text
   specify workflow run program-kit-bootstrap
   ```

3. Append only the requested `--input` arguments, including `initial_design` and normally `integration=codex` (or `integration=auto` when the initialized repository should decide).
4. Request execution of that outer command outside the current task sandbox. Explain that the workflow starts a nested Codex CLI which must manage its normal state outside the outer sandbox.
5. Ask the user to approve only that exact Program Kit prefix. They may choose **Always allow** for that exact prefix after review. Never propose `specify workflow`, a union of workflow IDs, a shell wrapper, an environment-variable assignment, or an arbitrary command prefix.

Run the exact command directly; do not wrap it in `powershell -Command`, `cmd /c`, a script, a pipeline, or a compound command, because Codex rules compare argument prefixes and conservatively handle shell wrappers.

For WSL, macOS, Linux, other integrations, or an ordinary terminal, run the same workflow command normally. If Codex cannot request outside-sandbox execution, tell the user to run it in an ordinary PowerShell terminal from the repository root.

## Guardrails

- Keep the preferred Windows elevated sandbox enabled.
- Do not redirect or copy Codex authentication, configuration, SQLite state, or app-server state into the project.
- Do not change `%USERPROFILE%\.codex` ACLs, enable global `danger-full-access`, or switch every workflow to the weaker unelevated sandbox.
- Do not install a Codex rule silently. The reviewable optional template is `.specify/extensions/program-kit-governance/templates/codex/program-kit-bootstrap.rules`.
- Do not auto-allow `specify workflow resume`. Assessment, constitution, and bootstrap resumes follow explicit human review gates and must remain prompted.

After the outer command pauses, report the run ID, the artifact to review, and the exact `specify workflow resume <run-id> --input <verdict>=<choice>` command. Never supply a human verdict on the user's behalf.
