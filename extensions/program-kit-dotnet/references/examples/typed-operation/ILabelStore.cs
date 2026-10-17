using System.Threading;
using System.Threading.Tasks;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Provider-neutral application port, placed in the consumer's Core project.</summary>
public interface ILabelStore
{
    /// <summary>Observes the committed sample value using the caller's cancellation.</summary>
    Task<string> ReadAsync(CancellationToken cancellationToken);
    /// <summary>Stores one value; a canceled/failed write may require reconciliation.</summary>
    Task WriteAsync(string value, CancellationToken cancellationToken);
}
