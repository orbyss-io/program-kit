using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;

namespace Orbyss.ProgramKit.Tasks.Diagnostics;

internal static class TaskDiagnostics
{
    internal static void Add(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string id,
        string message,
        string path) =>
        diagnostics.Add(
            new ProgramKitDiagnostic(
                id,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));

    internal static TaskCompositionException Exception(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        new(
            "The task registration set is invalid.",
            ProgramKitValidationResult.From(diagnostics));
}
