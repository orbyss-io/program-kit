using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

namespace Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

/// <summary>Fixture contract exposing reported material-free outcomes.</summary>
public interface IFixtureOutcomeSink : ISecretReactionOutcomeSink
{
    /// <summary>Gets a stable snapshot of reported outcomes.</summary>
    SecretReactionResult[] Results { get; }
}
