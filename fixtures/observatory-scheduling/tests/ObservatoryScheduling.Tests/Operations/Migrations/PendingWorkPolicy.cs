using Orbyss.ProgramKit.Artifacts.References;

namespace ObservatoryScheduling.Tests.Operations.Migrations;

internal sealed record PendingWorkPolicy(
    ArtifactReference ObservedTaskDefinition,
    ArtifactReference TargetTaskDefinition,
    PendingWorkDisposition Disposition,
    bool AllowObservedInstanceOnTargetHandler,
    ArtifactReference Evidence);
