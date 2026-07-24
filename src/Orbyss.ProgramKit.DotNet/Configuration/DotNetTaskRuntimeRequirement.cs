namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Exact task runtime and optional schedule provider required by a host.</summary>
public sealed record DotNetTaskRuntimeRequirement(
    [property: JsonPropertyName("runtimeRevision")] ArtifactReference RuntimeRevision,
    [property: JsonPropertyName("scheduleProviderRevisions")] ImmutableArray<ArtifactReference> ScheduleProviderRevisions);
