namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed record DotNetConsoleProjectionResult(
    DotNetConsoleHostProjection? Projection,
    ImmutableArray<ProgramKitDiagnostic> Diagnostics)
{
    internal bool IsValid =>
        Projection is not null &&
        Diagnostics.All(static diagnostic =>
            diagnostic.Severity != ProgramKitDiagnosticSeverity.Error);
}
