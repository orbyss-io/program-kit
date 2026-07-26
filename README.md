# Program Kit

`program-kit/` is the implemented, independently packageable architecture and
programming toolkit. It targets only .NET 10 and remains usable without the
Domain Semantic Engine. Program Kit runtime code does not depend on engine
domains, features, Lab code, or development-session capabilities.

The baseline includes universal artifacts, architecture/planning/quality and
development contracts, domainless modularity and model-first System.Text.Json
serialization, task meaning and in-process execution, scheduling with the
source-verified Cronos provider, deterministic Workbench projections, direct
CShells host composition, API/Console/Worker generation, CLI transport, local
package preparation/application publish, and the Observatory Scheduling
vertical proof.

Start with:

- [Final baseline review](artifacts/final/final-review-report.md)
- [Final topology and closure evidence](artifacts/final/README.md)
- [W080 self-hosted comparison](artifacts/self-hosted/README.md)
- [Observatory Scheduling fixture](fixtures/observatory-scheduling/README.md)
- [CLI commands](src/Orbyss.ProgramKit.CommandLine/README.md)
- [.NET generation contracts, including Aspire AppHost and optional FastEndpoints](src/Orbyss.ProgramKit.DotNet/README.md)
- [Deterministic Dev Container generation](src/Orbyss.ProgramKit.DevContainers/README.md)
- [Historical bootstrap authority](bootstrap/README.md)

The exact bootstrap design, plan, and separate approval record remain preserved
as implementation authority. The final review does not rewrite that history or
start a Release Cycle.
