using System.Collections.Concurrent;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

namespace Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

/// <summary>Consumer-owned material-free fixture outcome sink.</summary>
public sealed class FixtureOutcomeSink : IFixtureOutcomeSink
{
    private readonly ConcurrentQueue<SecretReactionResult> results = new();

    /// <summary>Gets a stable snapshot of reported outcomes.</summary>
    public SecretReactionResult[] Results => results.ToArray();

    /// <inheritdoc />
    public void Report(SecretReactionResult result)
    {
        ArgumentNullException.ThrowIfNull(result);
        results.Enqueue(result);
    }
}
