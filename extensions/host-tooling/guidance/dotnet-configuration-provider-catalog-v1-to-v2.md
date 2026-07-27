# .NET configuration-provider catalog migration from v1 to v2

Catalog v2 adds the `provider-polling` reload capability and the
`provider-polling-change-token` mechanism. Every v1 provider descriptor remains
representable without semantic change.

Only an exact reviewed provider revision may claim provider polling. Its
descriptor must state the package and generator revisions, whether polling may
be disabled, the provider-specific outage limitations, and the allowed secret
classifications. A consumer must not translate this mechanism into a general
atomic reload, rollback, availability, or rotation guarantee.

The initial v2 specialization is Azure Key Vault configuration provider 1.5.1.
Azure App Configuration is not part of this catalog revision because reviewed
packages failed the strict .NET 10 Microsoft.Extensions closure gate.
