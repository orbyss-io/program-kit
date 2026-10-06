# Application runtime and data requirements

Consumer-owned authoring input. Document only applicable implemented requirements. Identify dependency
capabilities and protocols; listening interfaces; read-only configuration/assets and writable paths;
startup/shutdown behavior; and actual implemented health surfaces. State absence of a health surface
or persistence explicitly rather than inventing either. Link actual tests/artifacts as evidence.

Foundation consumers use the existing application bundle and separately published digest-pinned host.
A feature, package, shell or API is not automatically a separate deployed process. Infrastructure
teams choose provisioning, topology and production orchestration independently.

When persistence exists, declare actual migration artifact/invocation/owner/application compatibility
in a small JSON descriptor referenced by the migrations category. Never promote local fixture
credentials into requirements; supported settings metadata contains classifications, not values.
