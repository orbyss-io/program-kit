using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Diagnostics;

public enum DiagnosticSeverity
{
    Info,
    Warning,
    Error,
    Fatal,
}

public enum DiagnosticCategory
{
    Request,
    Semantic,
    Resolution,
    Policy,
    Conformance,
    Workspace,
    External,
    Internal,
}

public sealed record Remediation(
    string Kind,
    IReadOnlyList<string> Targets,
    IReadOnlyList<string> Preconditions,
    RequestedEffect EffectClass,
    IReadOnlyList<string> AuthorityRequired,
    JsonObject? RequestDocument,
    ArtifactReference? RequestArtifact,
    IReadOnlyList<string>? RequestArguments,
    IReadOnlyList<string> Postconditions,
    OperationPhase RetryPhase);

public sealed record Diagnostic(
    string Id,
    GovernedIdentity Catalog,
    DiagnosticSeverity Severity,
    DiagnosticCategory Category,
    OperationPhase Phase,
    PrimaryDisposition Disposition,
    string OccurrenceKey,
    int OccurrenceCount,
    IReadOnlyList<string> Subjects,
    GovernedIdentity Rule,
    string MessageKey,
    IReadOnlyDictionary<string, SafeValue> Parameters,
    SafeValue Cause,
    SafeValue Consequence,
    SafeValue Expected,
    SafeValue Observed,
    IReadOnlyList<Remediation> Remediations,
    IReadOnlyList<EvidenceReference> Evidence);

public sealed record DiagnosticView(
    int Total,
    int Returned,
    int Omitted,
    string Grouping,
    string FullCollectionDigest,
    IReadOnlyList<Diagnostic> Items,
    ArtifactReference? FullCollectionArtifact = null);

public static class DiagnosticIds
{
    public const string MissingInput = "program-kit.kernel/PKREQ0001";
    public const string InvalidInput = "program-kit.kernel/PKREQ0002";
    public const string ConflictingInput = "program-kit.kernel/PKREQ0003";
    public const string ConflictingIdentity = "program-kit.kernel/PKSEM0001";
    public const string IncompleteMeaning = "program-kit.kernel/PKSEM0002";
    public const string MissingSelection = "program-kit.kernel/PKRES0001";
    public const string AmbiguousSelection = "program-kit.kernel/PKRES0002";
    public const string Incompatible = "program-kit.kernel/PKRES0003";
    public const string MissingAuthority = "program-kit.kernel/PKPOL0001";
    public const string InvalidWaiver = "program-kit.kernel/PKPOL0002";
    public const string GateFailed = "program-kit.kernel/PKCON0001";
    public const string DeterminismMismatch = "program-kit.kernel/PKCON0002";
    public const string GeneratedDrift = "program-kit.kernel/PKWSP0001";
    public const string Collision = "program-kit.kernel/PKWSP0002";
    public const string InterruptedPublication = "program-kit.kernel/PKWSP0003";
    public const string StaleSnapshot = "program-kit.kernel/PKWSP0004";
    public const string ExternalFailure = "program-kit.kernel/PKEXT0001";
    public const string ExternalUnavailable = "program-kit.kernel/PKEXT0002";
    public const string InternalFailure = "program-kit.kernel/PKINT0001";
    public const string DuplicateRoute = "program-kit.provider.dotnet/PKDOT0001";
    public const string MissingAssembler = "program-kit.provider.dotnet/PKDOT0002";
    public const string AmbiguousOrder = "program-kit.provider.dotnet/PKDOT0003";
    public const string CShellsConformance = "program-kit.provider.dotnet/PKDOT0004";
    public const string PackageMismatch = "program-kit.provider.dotnet/PKDOT0005";
    public const string DotNetToolFailure = "program-kit.provider.dotnet/PKDOT0006";
    public const string ForbiddenRuntimeDependency = "program-kit.provider.dotnet/PKDOT0007";
}
