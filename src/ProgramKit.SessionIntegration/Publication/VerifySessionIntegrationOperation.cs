using System;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed class VerifySessionIntegrationOperation
{
    private readonly SessionIntegrationServices services;

    public VerifySessionIntegrationOperation(SessionIntegrationServices services)
    {
        this.services = services;
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        services.SourceGuard.DemandConsumerWorkspace(workspaceRoot);
        SessionIntegrationCandidate candidate = new SessionIntegrationCandidateBuilder(services).Build(workspaceRoot, requestPath, SessionLifecycleOperation.Verify);
        SessionInstallationInspection inspection = new SessionInstallationStore(workspaceRoot, candidate.Provider.Manifest.ProviderIdentity.Name).Inspect();
        JsonObject session = SessionPayload.Candidate(candidate, Kebab(inspection.State), Kebab(inspection.SessionAvailability));
        session["observations"] = new JsonArray(inspection.Observations.Select(static observation => new JsonObject { ["logicalPath"] = observation.LogicalPath, ["expectedDigest"] = observation.ExpectedDigest, ["observedDigest"] = observation.ObservedDigest, ["state"] = observation.State }).ToArray());
        if (inspection.State is SessionIntegrationState.Exact or SessionIntegrationState.Absent)
            return OperationResultFactory.Success(PublicCommand.SessionVerify, OperationPhase.Completion, EffectState.None, candidate.RequestIdentity, session: session, disclosure: SessionPayload.Disclosure);

        Diagnostic diagnostic = DiagnosticFactory.Create(
            inspection.State == SessionIntegrationState.Drifted ? DiagnosticIds.GeneratedDrift : DiagnosticIds.InterruptedPublication,
            OperationPhase.Evaluation, "session-projection", "The admitted session integration does not match current live bytes.", "No mutation was performed; explain an exact repair request.");
        return OperationResultFactory.Failure(PublicCommand.SessionVerify, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Repair, new[] { diagnostic }, candidate.RequestIdentity) with { Session = session, Disclosure = SessionPayload.Disclosure };
    }

    private static string Kebab<T>(T value) where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));
}
