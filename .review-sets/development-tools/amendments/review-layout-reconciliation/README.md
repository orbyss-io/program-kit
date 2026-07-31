# Development Tools review-layout reconciliation

This amendment records the mechanical relocation of the approved Development
Tools review set from `extensions/development-tools/` to
`.review-sets/development-tools/` after Program Kit main commit
`11978dc6f3cbd66cd204214318eb166cb02c3e1c`.

The approved authority source, approval record, design, plan, and supporting
review artifacts retain their exact bytes and historical `extensions/...`
strings. Those strings describe the approval context; they are not live paths
and do not recreate the removed root.

`relocation-map.json` permits one finite prefix substitution only for artifact
paths declared by the frozen review manifest. `validate-relocation.ps1`
resolves each declared artifact, computes its Git-normalized LF SHA-256, and
refuses missing, duplicate, escaping, undeclared, or digest-mismatched content.

This amendment:

- changes no approved application, operation, MCP, capability, or provider
  semantics;
- grants no implementation, registration, initialization, permission,
  publication, or release authority;
- does not repair the approved alpha.3 plan's now-stale verification binding;
  a separately reviewed current-plan amendment remains required; and
- does not make the frozen validator a current-source implementation preflight.

Run `validate-relocation.ps1` from any working directory to verify the exact
