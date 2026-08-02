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
extension archive.

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
is a separate explicit `speckit.orbyss-program-kit-adapter.cleanup` operation and is limited to
unchanged, manifest-proven, regenerable adapter outputs.
