using System.Collections.Immutable;
using System.Globalization;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Diagnostics;

/// <summary>The immutable diagnostic catalog owned by Orbyss.ProgramKit.Architecture.</summary>
public static class ArchitectureDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable diagnostic identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
        CreateDefinitions();

    private static ImmutableArray<ProgramKitDiagnosticDefinition> CreateDefinitions()
    {
        var definitions = ImmutableArray.CreateBuilder<ProgramKitDiagnosticDefinition>();
        AddRange(definitions, 1, 7);
        AddRange(definitions, 100, 124);
        AddRange(definitions, 200, 212);
        AddRange(definitions, 300, 331);
        AddRange(definitions, 400, 407);
        AddRange(definitions, 500, 505);
        AddRange(definitions, 600, 640);
        AddRange(definitions, 700, 711);
        return definitions.DrainToImmutable();
    }

    private static void AddRange(
        ImmutableArray<ProgramKitDiagnosticDefinition>.Builder definitions,
        int first,
        int last)
    {
        for (var number = first; number <= last; number++)
        {
            var id = string.Create(
                8,
                number,
                static (span, value) =>
                {
                    "PKARC".AsSpan().CopyTo(span);
                    _ = value.TryFormat(
                        span[5..],
                        out _,
                        "D3",
                        CultureInfo.InvariantCulture);
                });
            definitions.Add(new ProgramKitDiagnosticDefinition(
                id,
                ProgramKitDiagnosticSeverity.Error,
                string.Concat("Architecture validation ", id)));
        }
    }
}
