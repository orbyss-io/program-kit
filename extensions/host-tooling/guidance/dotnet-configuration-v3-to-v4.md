# .NET shell configuration v3 to v4

This is a source-guidance migration. It selects reviewed configuration-provider
mechanics but never infers configuration meaning or secret-resolution behavior.

For every v3 configuration source:

1. Select the exact provider descriptor whose `kind` matches the source.
2. Replace `providerRevision` and `package` with that descriptor's exact
   identity, version, and digest. Reject an unavailable or ambiguous selection.
3. Add `initialValues: []` and `userSecretsId: null` to JSON, environment,
   command-line, and key-per-file sources.
4. Preserve source identity, order, path, prefix, optionality, startup,
   reload, secret-classification, and failure declarations only when the
   selected descriptor permits them.
5. Reject unsupported reload declarations, package drift, duplicate singleton
   providers, secret-classification mismatches, and development-only providers
   that are not optional and provider-owned.

In-memory, user-secrets, and chained-configuration sources are new in v4 and
require owner-authored values. They are never inferred from a v3 source.
Registered adapters require an explicitly reviewed catalog descriptor and
generator module; no type name, script, reflection, scanning, or ambient
provider discovery is accepted.

Configuration sources and secret resolvers remain separate selections. A
provider adapter may implement both contracts independently, but this migration
does not create or select a secret resolver.

An empty v3 configuration declaration migrates deterministically to the same
empty arrays under the v4 shell identity. Preserve the v3 source and report
stable diagnostics whenever an exact descriptor cannot be selected.
