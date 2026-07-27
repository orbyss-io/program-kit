namespace Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

internal static class WorkbenchDiagnostics
{
    internal static ProgramKitDiagnostic Error(
        string id,
        string message,
        string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);
}
