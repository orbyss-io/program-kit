# Exact Linux integration environment

This directory selects tooling for the separately human-started Keycloak
integration proof. It owns no Program Kit semantics and does not replace the
Aspire-backed fixture with direct Docker orchestration.

The Dockerfile composes the exact .NET SDK 10.0.302 Linux/amd64 manifest with
the exact Playwright 1.61.0 Noble Linux/amd64 manifest. Building or starting
the environment is deliberately not automated. Before an authorized
integration run, the runner must verify the derived image digest, the SDK,
the Chromium revision, access to one explicitly mounted compatible Docker
socket, and the absence of host-network or host-trust mutation.

The environment must remain disposable. It may receive the repository,
package cache, and container-runtime socket only through explicit
human-started bindings. It may not install host certificates, change host
networking, retain credentials or runtime files, or become a Program Kit
runtime dependency.
