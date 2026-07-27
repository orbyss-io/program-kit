using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Provider-adapter source of metadata-only lifecycle changes.</summary>
public interface ISecretChangeSource
{
    /// <summary>Subscribes one bounded callback for an exact stable reference identity.</summary>
    IDisposable Subscribe(
        ProgramKitIdentifier referenceIdentity,
        Action<SecretChangeSignal> callback);
}
