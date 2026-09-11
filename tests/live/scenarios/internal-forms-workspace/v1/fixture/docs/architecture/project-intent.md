# Internal Forms Workspace project intent

## Outcome

Maintain one existing workspace for secure internal, schema-driven forms. A .NET API owns HTTP form
contracts, a server-side BFF owns the browser session, a .NET Forms integration owns form composition,
and a React frontend renders the forms. The shared `default` CShell composes runtime features and the
Foundation host supplies the external runnable host.

## Existing topology

- `InternalForms.slnx` is the repository lock root.
- `InternalForms.Api` is the application API.
- `InternalForms.Bff` is the server-managed browser boundary.
- `InternalForms.Forms` integrates form and localization contracts.
- `web/package.json` is the consumer-owned React application.
- `shells.json` contains the shared `default` composition shell.
- `Dockerfile` is the host-image target.

The topology is accepted and must not be replaced. Its decision ID is
`decision-internal-forms-topology`.

## Accepted technology choices

The browser uses a server-managed BFF and cookies; no SPA token ownership is allowed. The decision ID
is `decision-server-managed-browser-session`. Forms use immutable JSON Forms contracts with the React
renderer. The decision ID is `decision-schema-driven-forms`.

The repository already owns Microsoft.OpenApi, React, React DOM, JSON Forms, TypeScript, and React type
packages. Program Kit must preserve those dependencies. Orbyss building blocks are not preselected or
preinstalled.

## Boundaries

Bootstrap records configuration knowledge but never credential values. No live browser, identity
provider, Docker daemon, Java viewer, frontend server, or complete product slice is required. The
acceptance surface is deterministic materialization, locked restore, compile, and narrow composition
probes.
