using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Planning.Diagnostics;

/// <summary>The immutable diagnostic catalog owned by Orbyss.ProgramKit.Planning.</summary>
public static class PlanningDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable diagnostic identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
        PlanningDiagnosticIds.All
            .Select(static id => new ProgramKitDiagnosticDefinition(
                id,
                ProgramKitDiagnosticSeverity.Error,
                string.Concat("Planning validation ", id)))
            .ToImmutableArray();
}
