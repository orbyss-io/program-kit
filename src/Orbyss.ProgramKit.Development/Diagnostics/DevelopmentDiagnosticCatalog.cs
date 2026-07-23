using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Development.Diagnostics;

/// <summary>The immutable diagnostic catalog owned by Orbyss.ProgramKit.Development.</summary>
public static class DevelopmentDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable diagnostic identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
        DevelopmentDiagnosticIds.All
            .Select(static id => new ProgramKitDiagnosticDefinition(
                id,
                ProgramKitDiagnosticSeverity.Error,
                string.Concat("Development validation ", id)))
            .ToImmutableArray();
}
