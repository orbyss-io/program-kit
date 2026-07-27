# Observatory Scheduling vertical proof

This fictional consumer proves that the Program Kit can compose one domain from
independently packaged features, generate API, Console, and Worker hosts, and
assess a real version migration without moving Observatory vocabulary into the
domainless Program Kit.

The source projects demonstrate:

- a contract-only Core that references Modularity, Serialization.JSON, and
  Tasks.Core;
- ordinary CShells features for visibility and observing constraints;
- one task-contributing scheduling feature with immediate, background, and
  scheduled execution;
- an endpoint-only API feature that contributes no task or service it does not
  own;
- explicit host runtime selections, health endpoints, JSON contributions, and
  package locks;
- an explicit host-to-CShell task-activation bridge that opens a tracked shell
  scope for every handler attempt while feature services remain shell-local;
- typed shell, lock, OpenAPI, Open Console, and Open Worker generation whose
  bytes repeat deterministically, including the Console dispatcher contract,
  document-bound dispatch lock, and dispatch evidence; and
- a typed v1-to-v2 Version Map assessment with an explicit, fixture-owned
  pending-work policy decision.

Fixture-owned workbench inputs and review evidence live below `artifacts/`.
The executable proof is in `tests/ObservatoryScheduling.Tests/`.
The runnable Observatory Console host remains hand-composed fixture behavior;
it is not the generated command-dispatch process proof. That proof belongs to
the isolated Program Kit `ConsoleCommandConsumer` conformance fixture.
This fixture proves that migration assessment cannot omit the pending-work
decision; it does not claim runtime enforcement. Tasks.Hosting activation
enforcement remains a later Program Kit work unit.
