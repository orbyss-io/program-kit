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
    IReadOnlyList<ProviderRole> Roles,
    IReadOnlyList<string> Profiles,
    IReadOnlyList<string> InputKinds,
    IReadOnlyList<string> OutputKinds,
    IReadOnlyList<string> Processes,
    IReadOnlyList<string> FilesystemEffects);

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

public interface IFactoryProvider
{
    ProviderManifest Manifest { get; }

    Task<ProviderConstructionResult> ConstructAsync(ProviderConstructionContext context);
}
