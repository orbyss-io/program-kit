using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.Contracts.Operations;

public enum PublicCommand
{
    Explain,
    Construct,
    Evaluate,
    SessionExplain,
    SessionInstall,
    SessionVerify,
    SessionRemove,
    Init,
    CatalogList,
    Restore,
    Prepare,
    AuthorityRecord,
    Help,
    Version,
}

public enum OperationOutcome
{
    Succeeded,
    NeedsInput,
    Blocked,
    Cancelled,
    Faulted,
}

public enum OperationPhase
{
    Request,
    Intake,
    Validation,
    Resolution,
    Explanation,
    Construction,
    Evaluation,
    Distribution,
    Workspace,
    Preparation,
    Authority,
    Publication,
    Admission,
    Completion,
}

public enum EffectState
{
    None,
    CandidateOnly,
    Committed,
    Indeterminate,
}

public enum PrimaryDisposition
{
    Complete,
    Retry,
    ProvideInput,
    RequestApproval,
    Repair,
    Revise,
    Stop,
}

public sealed record OperationChange(string Kind, string Subject, EffectState Effect);

public sealed record MissingInput(string Identity, string ValueKind, string RequiredAuthority, GovernedIdentity Rule);

public sealed record Continuation(
    string Schema,
    string CanonicalProfile,
    string RequestDigest,
    IReadOnlyList<MissingInput> MissingInputs,
    IReadOnlyDictionary<string, IReadOnlyList<string>> Choices,
    IReadOnlyList<string> AuthorityRequirements,
    string WorkspaceDigest,
    string EvidenceDigest,
    string Digest);

public sealed record OperationResult(
    string Schema,
    string CanonicalProfile,
    PublicCommand Command,
    GovernedIdentity OperationContract,
    string? RequestIdentity,
    string? ConstructionIdentity,
    OperationOutcome Outcome,
    OperationPhase FurthestPhase,
    EffectState EffectState,
    PrimaryDisposition PrimaryDisposition,
    IReadOnlyList<OperationChange> Changes,
    IReadOnlyList<ArtifactReference> Artifacts,
    IReadOnlyList<ArtifactReference> Receipts,
    IReadOnlyList<EvidenceReference> Evidence,
    DiagnosticView Diagnostics,
    Continuation? Continuation = null,
    JsonObject? Explanation = null,
    JsonObject? Utility = null,
    JsonObject? Session = null,
    IReadOnlyList<DisclosureEntry>? Disclosure = null,
    JsonObject? Payload = null);
