# Greeting CLI

Build a tiny local command-line application for a single user.

## Required behavior

- Use Python 3.13 and only its standard library.
- Running `python -m greeting` prints exactly `Hello, Program Kit!` followed by one newline.
- A successful invocation exits with code `0`.
- The application accepts no arguments. Supplying an argument prints a concise usage error to
  standard error and exits with code `2`.
- Automated tests verify the exact output and both exit-code paths.

## Explicit boundaries

- There is one local maintainer and no other actor or role.
- There is no browser interface, HTTP API, network access, identity, authorization, persistence,
  database, configuration file, secret, telemetry backend, deployment environment, background
  process, plugin, or third-party runtime dependency.
- Packaging, publication, installation, localization, accessibility, scaling, retention, backup,
  recovery, and production operation are outside this application.
- The first specification should cover the complete greeting journey rather than technical layers.
