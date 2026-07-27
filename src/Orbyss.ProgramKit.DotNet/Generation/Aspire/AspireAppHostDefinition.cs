namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>
/// Complete explicit input for one deterministic Aspire AppHost projection.
/// It owns no environment, deployment, or runtime-execution meaning.
/// </summary>
public sealed record AspireAppHostDefinition(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    ImmutableArray<AspireIntegrationSelection> Integrations,
    ImmutableArray<AspireParameterDefinition> Parameters,
    ImmutableArray<AspireResourceDefinition> Resources,
    ImmutableArray<AspireEndpointDefinition> Endpoints,
    ImmutableArray<AspireEnvironmentBinding> EnvironmentBindings,
    ImmutableArray<AspireResourceReference> References,
    ImmutableArray<AspireWaitDependency> WaitDependencies,
    ImmutableArray<AspireVolumeDefinition> Volumes);
