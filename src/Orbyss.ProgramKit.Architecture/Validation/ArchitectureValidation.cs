using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Validation;

internal static class ArchitectureValidation
{
    public static ImmutableArray<T> OrEmpty<T>(ImmutableArray<T> values) =>
        ArchitectureDiagnosticOperations.OrEmpty(values);

    public static bool IsDeclared(
        ProgramKitIdentifier identity,
        HashSet<string> declaredIds) =>
        !string.IsNullOrWhiteSpace(identity.Value) && declaredIds.Contains(identity.Value);

    public static void RequireDeclared(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ProgramKitIdentifier identity,
        HashSet<string> declaredIds,
        string path,
        string description)
    {
        diagnostics.Identifier(identity, path);
        if (!IsDeclared(identity, declaredIds))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc007,
                path,
                $"{description} '{identity.Value}' is not declared by this design.");
        }
    }
}
