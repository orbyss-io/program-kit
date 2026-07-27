using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

namespace Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

/// <summary>Fixture contract for a controllable metadata-only change source.</summary>
public interface IFixtureChangeSource : ISecretChangeSource
{
    /// <summary>Gets whether the generated subscription was disposed.</summary>
    bool SubscriptionDisposed { get; }

    /// <summary>Emits one metadata-only provider change.</summary>
    void Emit(SecretChangeSignal signal);
}
