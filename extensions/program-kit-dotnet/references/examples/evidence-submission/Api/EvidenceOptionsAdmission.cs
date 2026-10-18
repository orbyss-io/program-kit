using CShells.Lifecycle;
using Microsoft.Extensions.Options;

namespace ProgramKit.Examples.Evidence;

/// <summary>Required options are observed at actual shell activation, before any request/effect.</summary>
public sealed class EvidenceOptionsAdmission(IOptions<EvidenceApiOptions> options) : IShellInitializer
{
    /// <inheritdoc />
    public Task InitializeAsync(CancellationToken cancellation)
    {
        cancellation.ThrowIfCancellationRequested();
        _ = options.Value;
        return Task.CompletedTask;
    }
}
