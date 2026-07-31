# .NET shell configuration v2 to v3

This is a source-guidance migration. It does not infer configuration meaning.

For every v2 host:

1. Add `configurationSources` in exact provider-precedence order. Assign
   contiguous zero-based `order` values and declare provider revision, package,
   optionality, startup behavior, reload mechanics, secret classification, and
   failure behavior.
2. Replace each v2 configuration binding with a v3 typed binding. The component
   owner must supply definition identity/version, owner identity, namespace,
   Options type, section, exact schema, properties, defaults, examples,
   classifications, structural validation, and compatibility.
3. Select the exact source identities, Options name, fixed/snapshot/monitor
   consumption, consumer lifetime, startup validation, security classification,
   change reaction, and restart requirement.
4. Use `validateOnStart: true` for every required or security-critical binding.
5. Reject snapshot-to-singleton consumption, monitoring without a supported
   reload signal, live monitoring of restart-required topology, and any default
   or example for sensitive or secret-reference values.

An empty v2 `configurationBindings` array migrates deterministically to empty
`configurationSources` and `configurationBindings` arrays. Every non-empty v2
binding requires the missing owner-authored declarations before migration can
complete. Preserve the v2 source and report the missing declarations rather
than inventing them.
