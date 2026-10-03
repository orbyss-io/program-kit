# Windows workflow shell preflight

The dezaaglijst consumer's 0.12.3 report demonstrated Python direct lookup and
absolute execution succeeding with an inherited 8512-character PATH while cmd.exe
could resolve neither bare Python nor Node. Microsoft documents the 8191-character
command-processor limit, including inherited environment variables, in
[its command-line string limitation guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-client/shell-experience/command-line-string-limitation).
The native Windows regression reproduces this distinction.

Original worker preflight `9c70384f23224a7ca016185c43c14ee3` failed because the npm
Codex wrapper could not find Node; its generic workspace-write diagnostic pointed
at permissions. Native-executable preflight `bc60bde5a9e142b3ab879a40bf2b9620`
passed, but continuation `dae559cf-r-8dca6aa8` then failed at
`verify-recovery-source` because the workflow shell could not resolve bare Python.
These original records remain consumer evidence; source fixes do not rewrite them.

## Maintained source integration

The supplied `program-kit-windows-shell-preflight.patch` was checked against the
exact tagged v0.12.3 lifecycle source. Its normalized SHA-256 is
`0643b11d315f50ff633204386eeef4d3773fffdd30a28b7089f9fadd0dd391ce`.
`git apply --check --whitespace=error-all` passed in a disposable source copy.
The candidate incorporates the source-owned helper and regression tests, adapting
the lifecycle insertion to the existing coordinated Python-runtime correction.

`workflow_shell_preflight.verify_shell_launch` rejects an oversized inherited PATH
before selecting/probing any executable. It previews the exact existing Python
invocation environment through shared `python_runtime.invocation_values`, then
checks its length too: adding the selected interpreter's directory can push an
otherwise valid inherited PATH over the limit. It keeps all inherited directories.
No automatic bounded-tool policy, ecosystem-specific inventory or global PATH
change is introduced.

The model-free probe runs bare `python` with `subprocess.run(shell=True, env=...)`,
matching the installed Spec Kit ShellStep mode. It uses the recorded interpreter,
requires a structured marker and expected executable identity, and reports shell
failures with bounded, redacted root diagnostics under WORKFLOW_SHELL_PREFLIGHT.
Native tests compare the probe with an actual installed ShellStep execution.

Run, resume and reopen perform this check before CLI re-entry, product dependency
probes, worker policy, schema provisioning, execution locks, history snapshots or
state changes. The accepted interpreter binding then applies to all three entry
commands and restores the caller's environment on exit. Workspace-write policy,
managed requirements, semantic artifact validators and separate human approval
and ratification gates remain enforced.

## Consumer continuation

The consumer's local `Resume-Rm01Recovery.ps1` already selects a bounded process
PATH from resolved tools, verifies the installed shell adapter and restores its
caller's environment. The reported eight checks passed with a 672-character PATH,
including the original npm Codex wrapper. This is launch evidence; the linked
continuation's proof, review, human approval, readiness and engine-completion steps
still need to run. No feature-implementation success is inferred.

From the human-owned project terminal, when the operator intends to continue:

```powershell
& 'C:\Users\tech_\Code\dezaaglijst\.program-kit\evidence\Resume-Rm01Recovery.ps1'
```

For launch-only verification, its existing `-CheckOnly` option starts no workflow.
This task does not invoke either launcher mode, modify the installed consumer,
change saved workflow state or enable automatic approvals. Continue through the
existing lifecycle mapping; do not manually select a replacement child run.

Other consumers should use their human-owned resolved tool inventory for an explicit
invocation environment. Include only tools their selected workflow needs and restore
the original process environment afterward. Keep this generic across ecosystems;
the dezaaglijst .NET/browser inventory is not a Program Kit default. Broad automatic
environment construction remains a separate policy decision.

## Validation and release

The 12 targeted shell tests passed on native Windows: the original seven cases,
projected-PATH overflow, actual installed ShellStep parity, recorded-runtime binding,
exit-zero malformed/missing markers and timeout diagnostics. Oversized PATH run,
resume and reopen leave disposable state/history byte-identical and never call
runtime, worker, schema or lock operations. The five existing runtime tests and
worker-policy fixture validator passed. Tests start no coding worker or model API.
The bounded Development suite passed all 61 checks. Its working-tree validation
journal is `artifacts/validation-runs/20261003T001102Z-7d100bc2/journal.json`;
this is development evidence, not an exact-commit publication receipt.

This correction is included in the unreleased 0.12.4 candidate. The combined
candidate still requires the released coordinated Spec Kit dependency, updated
actual pins and fresh full Release validation in the user-owned terminal described
in [the release guide](releasing-0.12.4.md). Preserve existing release evidence and
keep Firefox in CI; do not publish or claim consumer recovery completion from these
development checks.
