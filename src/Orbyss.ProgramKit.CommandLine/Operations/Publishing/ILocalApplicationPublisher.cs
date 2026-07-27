namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Publishes one exact generated host from a verified local package root.</summary>
public interface ILocalApplicationPublisher
{
    /// <summary>Generates, locks, restores, publishes, and manifests one selected host.</summary>
    ValueTask<LocalApplicationPublishResult> PublishAsync(
        LocalApplicationPublishRequest request,
        CancellationToken cancellationToken);
}
