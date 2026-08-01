using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed class RemoveSessionIntegrationOperation
{
    private readonly SessionIntegrationServices services;
    private readonly SessionRemovalJournal removal;

    public RemoveSessionIntegrationOperation(SessionIntegrationServices services, SessionRemovalJournal? removal = null)
    {
        this.services = services;
        this.removal = removal ?? new SessionRemovalJournal();
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        services.SourceGuard.DemandConsumerWorkspace(workspaceRoot);
        SessionIntegrationCandidate candidate = new SessionIntegrationCandidateBuilder(services).Build(workspaceRoot, requestPath, SessionLifecycleOperation.Remove);
        string providerName = candidate.Provider.Manifest.ProviderIdentity.Name;
        SessionInstallationStore store = new(workspaceRoot, providerName);
        SessionInstallationInspection inspection = store.Inspect();
        if (inspection.State == SessionIntegrationState.Removed)
            return OperationResultFactory.Success(PublicCommand.SessionRemove, OperationPhase.Completion, EffectState.None, candidate.RequestIdentity, session: State(candidate, "removed", "not-evaluated"), disclosure: SessionPayload.Disclosure);
        if (inspection.State == SessionIntegrationState.Absent || inspection.Record is null)
            return Failure(candidate, SessionDiagnosticCatalog.Id(8), PrimaryDisposition.ProvideInput, "No exact admitted installation record is present.", inspection.State);
        if (inspection.State == SessionIntegrationState.Drifted)
            return Failure(candidate, SessionDiagnosticCatalog.Id(4), PrimaryDisposition.Repair, "An admitted projection is drifted; removal refused every file.", inspection.State);
        if (inspection.State != SessionIntegrationState.Exact)
            return Failure(candidate, SessionDiagnosticCatalog.Id(5), PrimaryDisposition.Repair, "Complete trusted installation state cannot be proven; removal refused every file.", inspection.State);

        RequestBoundAuthorityGrant grant = LoadGrant(workspaceRoot, candidate, store);
        services.Authority.Demand(new AuthorityDemand(
            candidate.Request.Workspace.Identity.StableKey, "session-remove", RequestedEffect.Committed, candidate.RequestCoreIdentity,
            candidate.Provider.Manifest.ProviderIdentity.StableKey, candidate.Request.Scope, candidate.Request.EvaluationContext.Instant), grant);

        SessionRemovalResult result;
        try
        {
            result = removal.Remove(workspaceRoot, providerName, inspection.Record);
        }
        catch (Exception)
        {
            return Failure(candidate, SessionDiagnosticCatalog.Id(5), PrimaryDisposition.Repair, "Removal did not complete; inspect the removal journal and verify the installation before retrying.", store.Inspect().State, EffectState.Indeterminate);
        }
        store.MarkGrantConsumed(grant.GrantIdentity, candidate.RequestIdentity);
        JsonObject session = State(candidate, "removed", "not-evaluated");
        session["removalJournal"] = result.JournalLogicalPath;
        session["removalReceipt"] = result.ReceiptLogicalPath;
        session["removalReceiptDigest"] = result.ReceiptDigest;
        return OperationResultFactory.Success(
            PublicCommand.SessionRemove, OperationPhase.Completion, EffectState.Committed, candidate.RequestIdentity, inspection.Record.InstallationIdentity.Digest,
            session: session, disclosure: SessionPayload.Disclosure, changes: result.Changes);
    }

    private static OperationResult Failure(SessionIntegrationCandidate candidate, string id, PrimaryDisposition disposition, string cause, SessionIntegrationState state, EffectState effect = EffectState.None)
    {
        Diagnostic diagnostic = SessionDiagnosticFactory.Create(id, OperationPhase.Evaluation, "session-removal", cause);
        return OperationResultFactory.Failure(PublicCommand.SessionRemove, OperationOutcome.Blocked, OperationPhase.Evaluation, effect, disposition, new[] { diagnostic }, candidate.RequestIdentity) with
        {
            Session = State(candidate, Kebab(state), "not-evaluated"),
            Disclosure = SessionPayload.Disclosure,
        };
    }

    private static JsonObject State(SessionIntegrationCandidate candidate, string state, string availability) => SessionPayload.Candidate(candidate, state, availability);

    private static RequestBoundAuthorityGrant LoadGrant(string workspaceRoot, SessionIntegrationCandidate candidate, SessionInstallationStore store)
    {
        if (candidate.AuthorityGrantLogicalPath is null) throw new UnauthorizedAccessException("The removal request has no exact authority grant reference.");
        string grantPath = LogicalPaths.ResolveInside(workspaceRoot, candidate.AuthorityGrantLogicalPath);
        if (!File.Exists(grantPath)) throw new UnauthorizedAccessException("The exact removal authority grant artifact is unavailable.");
        JsonObject document = CanonicalJson.Parse(File.ReadAllBytes(grantPath)).AsObject();
        GovernedIdentity identity = ParseIdentity(document["identity"]!.AsObject());
        JsonObject validity = document["validity"]!.AsObject();
        return new RequestBoundAuthorityGrant(
            "program-kit.request-bound-authority-grant/v1", identity.StableKey, candidate.Request.Workspace.Identity.StableKey,
            document["operations"]!.AsArray().Select(static value => value!.GetValue<string>()).Single(),
            document["effects"]!.AsArray().Select(static value => value!.GetValue<string>()).Single(),
            document["requestBinding"]!.GetValue<string>(), Condition(document, "provider"), Condition(document, "scope"),
            ParseInstant(validity["notBefore"]!.GetValue<string>()), ParseInstant(validity["notAfter"]!.GetValue<string>()), false, store.IsGrantConsumed(identity.StableKey));
    }

    private static string Condition(JsonObject grant, string kind) => grant["conditions"]!.AsArray().Select(static value => value!.AsObject()).Single(item => string.Equals(item["kind"]!.GetValue<string>(), kind, StringComparison.Ordinal))["value"]!["value"]!.GetValue<string>();
    private static DateTimeOffset ParseInstant(string value) => DateTimeOffset.ParseExact(value, "yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
    private static GovernedIdentity ParseIdentity(JsonObject value) => new(value["authority"]!.GetValue<string>(), value["kind"]!.GetValue<string>(), value["name"]!.GetValue<string>(), value["revision"]!.GetValue<string>(), value["digest"]!.GetValue<string>());
    private static string Kebab<T>(T value) where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));
}
