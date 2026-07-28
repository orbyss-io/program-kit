namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Refreshes generated hosts from committed exact generation requests.</summary>
public interface IDotNetHostRefreshService
{
    /// <summary>Previews or performs one exact host refresh.</summary>
    ValueTask<DotNetHostRefreshResult> RefreshAsync(
        string requestPath,
        bool preview,
        bool buildConsumer,
        bool repairGeneratedOutput,
        CancellationToken cancellationToken);
}
