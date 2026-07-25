namespace Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

/// <summary>The immutable Operations diagnostic catalog.</summary>
public static class OperationsDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
        OperationsDiagnosticIds.All
            .Select(static id => new ProgramKitDiagnosticDefinition(
                id,
                ProgramKitDiagnosticSeverity.Error,
                string.Concat("Operations validation ", id)))
            .ToImmutableArray();
}
