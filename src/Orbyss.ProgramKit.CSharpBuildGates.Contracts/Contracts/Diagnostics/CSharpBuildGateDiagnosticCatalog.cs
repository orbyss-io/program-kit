using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;

/// <summary>The immutable mechanics diagnostic catalog owned by Program Kit.</summary>
public static class CSharpBuildGateDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
        CSharpBuildGateDiagnosticIds.All
            .Select(static id => new ProgramKitDiagnosticDefinition(
                id,
                ProgramKitDiagnosticSeverity.Error,
                string.Concat("C# build-gate contract validation ", id)))
            .ToImmutableArray();
}
