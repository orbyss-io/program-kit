# Program Kit Adapter for Spec Kit

This extension connects reviewed Spec Kit feature artifacts to the public
Program Kit CLI without granting authority or coupling to Program Kit internals.

The extension requires Spec Kit `0.15.1`, Program Kit CLI
`1.0.0-alpha.2`, and the .NET 10 runtime. Its project configuration is copied
from `config/orbyss-program-kit-adapter-config.template.yml` to the exact
consumer-owned path documented by Spec Kit. Local and environment configuration
layers are deliberately non-semantic.

This source directory contains no generated binary. `eng/Pack-SpecKitAdapter.ps1`
publishes the adapter into an ignored staging directory and creates the tested
extension archive. The archive also exposes its exact compatibility manifest,
diagnostic catalog, public schemas, and release-file closure for inspection.

## Consumer flow

1. Initialize Spec Kit and install `Orbyss.ProgramKit.Cli@1.0.0-alpha.2` as a
   workspace-local .NET tool.
2. Run Program Kit `init`, inspect `catalog list`, add an exact profile selection
   to the consumer-owned `program-kit.yaml`, and run a factory restore.
3. Install with `specify extension add orbyss-program-kit-adapter` from the
   configured exact catalog and keep the generated project configuration under
   version control.
4. Run the normal Spec Kit feature workflow. Documentation-only, disabled, or
   explicitly non-applicable work stays inactive and invokes no Program Kit
   child process.
5. For applicable factory work, review the complete handoff before validate,
   prepare, and explain. A human or agent may invoke the commands, but an LLM
   proposal is not semantic authority.
6. After reviewing the prepared artifact set, invoke the Program Kit
   `authority record` command separately. Supply its exact grant to construct,
   then evaluate the result.

Workspace defaults are recorded only in `program-kit.yaml`; a feature override
may select another exact locked alias. A reviewed handoff pins the effective
selection and reports default drift instead of silently rebinding.

## Lifecycle and ownership

Spec Kit owns extension registration and the installed extension directory.
The packaged configuration template is adapter-release-owned, but the
top-level `orbyss-program-kit-adapter-config.yml` created from it is
consumer-owned. Update, disable, and re-enable do not authorize construction or
cleanup. Re-enable changes registration only; every later adapter operation
revalidates the workspace before use.

Remove with the supported preservation path:

```text
specify extension remove orbyss-program-kit-adapter --keep-config
```

That removal leaves the consumer configuration, feature handoffs and reviews,
Program Kit state, products, receipts, and evidence in place. Candidate cleanup
is a separate explicit `speckit.orbyss-program-kit-adapter.cleanup` operation
and is limited to unchanged, manifest-proven, regenerable adapter outputs.

## Honest limitations

Release `0.1.0` supports only Spec Kit `0.15.1`, Program Kit
`1.0.0-alpha.2`, .NET 10, and the compiled
`dotnet10-cshells-0.0.28@1.0.0` profile on Windows and Linux. It translates one
component/API definition family and preserves referenced custom source as
consumer-owned. It does not infer arbitrary prose, select a provider, grant
authority, plan a feature, migrate existing code, load downloaded providers,
use global tools, or make custom implementation deterministic.
