# Internal Forms Workspace request

Bootstrap an existing repository named **Internal Forms Workspace**. Preserve the supplied solution,
three .NET projects, frontend package, shared CShell file, Dockerfile, and every consumer-owned
dependency. Do not replace the topology or create another application boundary.

The workspace has an HTTP API, a server-managed BFF browser boundary, a .NET Forms integration, and
a React frontend that renders immutable schema-driven forms. The application uses the Foundation
host and one shared CShell named `default`. Authentication values belong to deployment; record
configuration knowledge and sensitivity, but do not create credentials or runtime values.

The accepted architecture decisions must use these exact IDs:

- `decision-internal-forms-topology`
- `decision-server-managed-browser-session`
- `decision-schema-driven-forms`

Bootstrap only. Do not implement a product slice, start a browser, viewer, container, identity
provider, Java process, or development server. The existing compile probes are the consumer-owned
application surface. This request is complete and confirmed; stop rather than inventing additional
requirements.
