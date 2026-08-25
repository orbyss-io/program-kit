# Example initial design

Build a service that accepts configuration definitions through an HTTP API, resolves source inputs, produces immutable configuration packages, signs them, and publishes them to an OCI registry. A .NET client downloads and atomically activates packages. The service uses .NET, PostgreSQL, and a React/TypeScript UI.

The design does not yet decide tenant isolation, authorization policy, build sandboxing, queue/outbox delivery semantics, API and event versioning, package path and size limits, source reproducibility, signing authority, recovery objectives, or how clients observe activation failures.

