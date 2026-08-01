using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.SessionIntegration.Diagnostics;

public static class SessionRemediationProjector
{
    public static JsonObject Project(string diagnosticId)
    {
        SessionDiagnosticDefinition definition = SessionDiagnosticCatalog.Get(diagnosticId);
        return new JsonObject
        {
            ["diagnosticId"] = definition.Id,
            ["disposition"] = definition.Disposition,
            ["retryable"] = definition.Retryable,
            ["action"] = definition.SafeRemediation,
            ["requiresNewRequest"] = definition.Disposition is "repair" or "revise" or "provide-input",
        };
    }
}
