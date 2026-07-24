namespace Orbyss.ProgramKit.Tasks.Core.Results;

/// <summary>Typed successful response pinned to its exact response contract.</summary>
/// <typeparam name="TResponse">The consumer-owned typed response model.</typeparam>
public sealed record TaskResponse<TResponse>(
    ArtifactReference Revision,
    ArtifactReference InstanceRevision,
    ArtifactReference ResponseContract,
    DateTimeOffset CompletedAt,
    TResponse Payload)
    where TResponse : notnull;
