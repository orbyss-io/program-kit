using System.Threading;
using System.Threading.Tasks;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Application-owned orchestration; this example promises no atomic write/read snapshot or retry.</summary>
public sealed class LabelOperations(ILabelStore store) : ILabelOperations
{
    /// <inheritdoc />
    public Task<string> ReadAsync(CancellationToken cancellationToken) => store.ReadAsync(cancellationToken);

    /// <inheritdoc />
    public async Task<string> UpdateAsync(string value, CancellationToken cancellationToken)
    {
        await store.WriteAsync(value, cancellationToken);
        return await store.ReadAsync(cancellationToken);
    }
}
