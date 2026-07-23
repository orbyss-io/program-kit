using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;

namespace Orbyss.ProgramKit.Modularity.Diagnostics;

internal static class ModularityDiagnostics
{
    internal static ProgramKitDiagnostic Error(
        string id,
        string message,
        string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);

    internal static ProgramKitValidationResult Result(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        ProgramKitValidationResult.From(diagnostics);
}
