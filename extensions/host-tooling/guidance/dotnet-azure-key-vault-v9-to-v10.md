# .NET Azure Key Vault migration from shell v9 to v10

Shell v10 adds an optional, exact Azure Key Vault configuration composition.
Existing v9 hosts migrate with `azureConfiguration` absent or `null` and retain
their prior behavior.

An enabled composition binds every selected Key Vault configuration source to
the reviewed provider and generator revisions, one HTTPS vault endpoint, one
classified credential-resolution contract, a bounded resolution timeout, an
optional positive polling interval, and mandatory operational-metadata
redaction. Canonical input contains references and endpoint identity, never
credential or secret values.

Generated hosts require a consumer-owned partial credential resolver returning
an `Azure.Core.TokenCredential`. Program Kit does not choose a credential
implementation, inspect the current user, or perform ambient identity
discovery. The generated active-secret manager excludes disabled, expired, and
not-yet-valid secrets. Reloading uses the provider's exact polling behavior and
must not be generalized into an atomic rotation or outage guarantee.

Azure App Configuration remains absent from shell v10. Stable 8.5.0 and
8.6.0-preview were both rejected because actual provider API compilation under
the Program Kit Microsoft.Extensions 10 closure emits CS1701
assembly-unification warnings. No warning suppression, dependency downgrade,
shim, reflection activation, or provider reimplementation is authorized.
