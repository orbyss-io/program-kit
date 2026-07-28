namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Publishes and recovers complete sealed generated roots.</summary>
public interface IGeneratedOutputPublisher
{
    /// <summary>Stages, seals, verifies, and publishes one absent generated root.</summary>
    ValueTask<GeneratedOutputSeal> PublishCreateAsync(
        string rootPath,
        IEnumerable<GeneratedOutputPayload> payloads,
        CancellationToken cancellationToken);

    /// <summary>Completes an interrupted ready transaction without regenerating.</summary>
    ValueTask RecoverAsync(
        string rootPath,
        CancellationToken cancellationToken);
}
