using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Quality.Diagnostics;

/// <summary>The immutable diagnostic catalog owned by Orbyss.ProgramKit.Quality.</summary>
public static class QualityDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable diagnostic identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
        QualityDiagnosticIds.All
            .Select(static id => new ProgramKitDiagnosticDefinition(
                id,
                ProgramKitDiagnosticSeverity.Error,
                string.Concat("Quality validation ", id)))
            .ToImmutableArray();
}
