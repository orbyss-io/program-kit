# Program Kit 0.9.1 evidence

The release regression matrix covers:

- clean `none`, BFF-cookie, and SPA-PKCE installs plus every directed profile transition;
- a profile-neutral Keycloak base and one exact selected-client contribution, with no disabled or
  retained alternative client;
- BFF session establishment requiring non-empty validated issuer and subject claims;
- authenticated structured removal of legacy root web settings and zero mutation for customized values;
- consumer edits to shell activation/configuration, host settings, and OpenAPI registry with clean
  `--check` exit semantics;
- runnable-host descriptors validated against the shipped closed schema with a present or absent
  profile overlay;
- consumer verification-hook fallback, execution, failure propagation, preservation, and fixed-path safety;
- TypeScript compilation and runtime tests of the managed BFF logout adapter.

The OpenAPI producer/contract registry, feature metadata, toolchain evidence, profile records, and
managed-state schemas were audited alongside runnable-host output; no second undeclared producer
field was found.
