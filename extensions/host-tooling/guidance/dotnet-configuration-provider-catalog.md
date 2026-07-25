# .NET configuration provider catalog 1.0.0

The provider catalog is a finite design-time contract. A shell selects one
provider by exact identity, version, and digest; it does not name an arbitrary
.NET type, assembly, script, or service-container key. The matching generator
is supplied explicitly through `IDotNetConfigurationProviderComposition`.
There is no reflection, assembly scanning, ambient discovery, or runtime
dependency on Program Kit generation assemblies.

Catalog 1.0.0 contains these reviewed .NET 10.0.10 projections:

- JSON file;
- environment variables;
- command line;
- in-memory public values;
- development-only user secrets;
- key-per-file;
- an explicitly generated, secret-free chained configuration root.

Each descriptor pins its package and generator revisions and declares its
reload capabilities, reload mechanism, development restriction, accepted
secret classification, and operational limitations. JSON, user-secrets, and
key-per-file reload through file-provider change tokens. Filesystem
notifications can be delayed, coalesced, or absent on container bind mounts
and network shares. ABI 1.0.0 does not generate polling.

Provider ordering is the shell source order and therefore configuration
precedence. Orders are contiguous and zero based. Duplicate exact provider
selections, conflicting singleton providers, package drift, unsupported
reload declarations, invalid initial values, and secret-classification
mismatches fail with stable diagnostics.

In-memory and chained values are owner-authored public configuration only.
User secrets are optional, provider-owned, and guarded by the Development
environment. Key-per-file and environment variables may carry provider-owned
values because Program Kit emits only their source mechanics, never their
values. Generated provider-binding evidence includes keys, capability data,
and limitations, but not initial values or a user-secrets identifier.

Configuration providers and secret resolvers are separate contracts. An
adapter may implement both independently, but registering one never registers
or selects the other. Secret rotation reactions remain the responsibility of
the secret-resolution contract and the consuming component.

Third-party adapters use `RegisteredAdapter` only after a reviewed descriptor
and generator implementation are passed explicitly to the composition
factory. The registry requires one exact generator for every descriptor and
rejects unknown revisions.
