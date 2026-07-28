# Reusable C# build-gate compatibility matrix

This exact matrix binds the independent clocks for Architecture v2, Planning
v3, the static-conformance disposition, gate contracts, public Program Kit
contract analyzers, consumer-owned analyzers, authoring recipes, build
mechanics, deterministic operations, capabilities, CapabilityBundle
0.1.0-alpha.2, the
pinned toolchain, selection locks, and evidence.

`compatibility-version-matrix.json` is the machine-readable source. Every
selection is an exact version and SHA-256 digest. Floating, mixed, partial, and
stale selections fail closed. A component changes on its own clock; every
dependent edge must then be reviewed and rebound explicitly.

Architecture v1 and Planning v2 remain readable only through their explicit,
human-decision-requiring migrations. The migrations do not infer a
static-conformance disposition or gate selection.

The repository-local `EngineLikeGateConsumer` fixture is fictional. It uses no
source or inferred semantics from the Domain Semantic Engine repository. Its
non-packable consumer-owned analyzer adopts the exact
`forbid-type-name-suffix@1.0.0` recipe and separately selects the public
generated-source contract analyzer. It does not select Program Kit's private
analyzer and receives no general code-generation authority; its only generator
is the narrow same-assembly participation receipt required by the gate.
