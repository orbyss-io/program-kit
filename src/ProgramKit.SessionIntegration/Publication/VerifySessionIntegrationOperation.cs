using System;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

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
        if (inspection.State == SessionIntegrationState.Exact)
        {
            Diagnostic availability = SessionDiagnosticFactory.Create(SessionDiagnosticCatalog.Id(9), OperationPhase.Completion, "provider-session-availability", "A fresh provider session has not yet supplied discovery evidence.");
            return OperationResultFactory.Success(PublicCommand.SessionVerify, OperationPhase.Completion, EffectState.None, candidate.RequestIdentity, session: session, disclosure: SessionPayload.Disclosure) with
            {
                PrimaryDisposition = PrimaryDisposition.Retry,
                Diagnostics = Orbyss.ProgramKit.Kernel.Diagnostics.DiagnosticFactory.View(new[] { availability }),
            };
        }

        if (inspection.State == SessionIntegrationState.Absent)
        {
            Diagnostic missing = SessionDiagnosticFactory.Create(SessionDiagnosticCatalog.Id(8), OperationPhase.Evaluation, "session-installation-record", "No exact admitted installation record is present.");
            return OperationResultFactory.Failure(PublicCommand.SessionVerify, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.ProvideInput, new[] { missing }, candidate.RequestIdentity) with { Session = session, Disclosure = SessionPayload.Disclosure };
        }

        string diagnosticId = inspection.State == SessionIntegrationState.Drifted ? SessionDiagnosticCatalog.Id(4) : SessionDiagnosticCatalog.Id(5);
        Diagnostic diagnostic = SessionDiagnosticFactory.Create(
            diagnosticId, OperationPhase.Evaluation, "session-projection", "The admitted session integration does not match current live bytes.");
        return OperationResultFactory.Failure(PublicCommand.SessionVerify, OperationOutcome.Blocked, OperationPhase.Evaluation, EffectState.None, PrimaryDisposition.Repair, new[] { diagnostic }, candidate.RequestIdentity) with { Session = session, Disclosure = SessionPayload.Disclosure };
    }

    private static string Kebab<T>(T value) where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));
}
