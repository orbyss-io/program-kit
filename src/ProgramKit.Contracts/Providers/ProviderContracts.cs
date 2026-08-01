using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Providers;

public enum ProviderRole
{
    IntakeMapping,
    Construction,
    Evaluation,
}

public sealed record ProviderManifest(
    GovernedIdentity Identity,
    GovernedIdentity Distribution,
    IReadOnlyList<ProviderRole> Roles,
    IReadOnlyList<string> Profiles,
    IReadOnlyList<string> InputKinds,
    IReadOnlyList<string> OutputKinds,
    IReadOnlyList<string> Processes,
    IReadOnlyList<string> FilesystemEffects);

public sealed record ProviderIntakeContext(
    string WorkspaceRoot,
    JsonObject RootBundle,
    string RequestDigest,
    CancellationToken CancellationToken);

public sealed record ProviderIntakeResult(
    JsonObject Definition,
    IReadOnlyList<ArtifactReference> Inputs,
    IReadOnlyList<JsonObject> Evidence,
    IReadOnlyList<string> Diagnostics,
    bool Succeeded);

public sealed record ProviderConstructionContext(
    string WorkspaceRoot,
    string CandidateRoot,
    string DependencyMirrorRoot,
    JsonObject Definition,
    string ConstructionIdentity,
    CancellationToken CancellationToken);

public sealed record ProviderArtifact(
    string LogicalPath,
    ArtifactOwnership Ownership,
    string MediaType,
    ClaimClass ClaimClass,
    string ProducerIdentity);

public sealed record ProviderConstructionResult(
    IReadOnlyList<ProviderArtifact> Artifacts,
    IReadOnlyList<JsonObject> Evidence,
    IReadOnlyList<string> Diagnostics,
    bool Succeeded);
public sealed record ProviderEvaluationContext(
    string WorkspaceRoot,
    JsonObject Definition,
    string ClosureDigest,
    string? ConstructionIdentity,
    CancellationToken CancellationToken);

public sealed record ProviderEvaluationResult(
    IReadOnlyList<JsonObject> Evidence,
    IReadOnlyList<string> Diagnostics,
    bool Succeeded);


public interface IFactoryProvider
{
    ProviderManifest Manifest { get; }
}

public interface IIntakeMappingProvider : IFactoryProvider
{
    Task<ProviderIntakeResult> MapAsync(ProviderIntakeContext context);
}

public interface IConstructionProvider : IFactoryProvider
{
    Task<ProviderConstructionResult> ConstructAsync(ProviderConstructionContext context);
}

public interface IEvaluationProvider : IFactoryProvider
{
    Task<ProviderEvaluationResult> EvaluateAsync(ProviderEvaluationContext context);
}
