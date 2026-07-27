using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>Complete deterministic Keycloak fixture output set and tree digest.</summary>
public sealed record KeycloakLocalFixtureGenerationResult(
    ImmutableArray<GeneratedOutput> Outputs,
    Sha256Digest OutputTreeSha256);
