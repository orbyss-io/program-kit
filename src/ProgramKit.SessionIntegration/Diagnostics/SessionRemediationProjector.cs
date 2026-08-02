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
            ["disposition"] = SessionDiagnosticCatalog.Kebab(definition.Disposition),
            ["retryable"] = definition.Retryable,
            ["action"] = definition.SafeRemediation,
            ["requiresNewRequest"] = definition.Disposition is Orbyss.ProgramKit.Contracts.Operations.PrimaryDisposition.Repair
                or Orbyss.ProgramKit.Contracts.Operations.PrimaryDisposition.Revise
                or Orbyss.ProgramKit.Contracts.Operations.PrimaryDisposition.ProvideInput,
        };
    }
}
