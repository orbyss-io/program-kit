using System.Threading;
using System.Threading.Tasks;
using CShells.Lifecycle;
using Microsoft.Extensions.Options;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Admits required API options during shell preparation without resolving runtime effects.</summary>
[LifecycleOrder(LifecyclePhase.Prepare, -1000)]
internal sealed class LabelApiOptionsAdmission(IOptions<LabelApiOptions> options) : IShellInitializer
{
    /// <inheritdoc />
    public Task InitializeAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _ = options.Value;

        return Task.CompletedTask;
    }
}
