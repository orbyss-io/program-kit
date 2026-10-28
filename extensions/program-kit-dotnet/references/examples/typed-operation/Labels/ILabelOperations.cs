using System.Threading;
using System.Threading.Tasks;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Owned label use cases, independent of HTTP and the selected storage implementation.</summary>
public interface ILabelOperations
{
    /// <summary>Reads the current label.</summary>
    Task<string> ReadAsync(CancellationToken cancellationToken);
    /// <summary>Updates the label and observes its current committed representation.</summary>
    Task<string> UpdateAsync(string value, CancellationToken cancellationToken);
}
