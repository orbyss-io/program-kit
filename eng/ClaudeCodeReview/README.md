# Claude Code isolated review kit

This sealed kit evaluates one exact provider surface:
`anthropic:session-provider:claude-code@2.1.220`. It contains a packaged Program
Kit CLI, bounded fixtures, schemas, and review scripts. It contains no Program
Kit source, Spec Kit, credentials, authority grant, prompt transcript, model
reasoning, or raw provider output.

The current Feature 003 kit is intentionally fail-closed: Feature 002 product
acceptance is rejected, so the Claude adapter support claim is `not-evaluated`.
`Initialize-ConsumerWorkspace.ps1` and
`Invoke-DeterministicConsumerProof.ps1` may be used to verify the sealed kit and
ten repeatable no-effect consumer trials. `Invoke-ClaudeCodeTrials.ps1` refuses
to launch Claude until a newly sealed kit binds both an accepted canonical
dependency and a supported adapter, plus explicit current human authority.

Initialization accepts only Windows or Linux with exact .NET SDK `10.0.302`,
an absent or empty consumer root, and no Program Kit/Spec Kit/Codex/Claude
projection or prior session lifecycle state. The manifest binds the CLI
package, provider, adapter, canonical definition, diagnostics, schemas, and
the exact shared conformance corpus in addition to every sealed file.

Provider installation, authentication, workspace trust, network access, and
process permission remain separately managed by the human. None of them grants
Program Kit effect authority. Never edit the kit after export; a changed byte
invalidates its manifest digest.
