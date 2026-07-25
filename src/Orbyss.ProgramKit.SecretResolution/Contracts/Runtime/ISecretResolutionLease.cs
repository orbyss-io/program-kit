using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Base disposable lease for one typed protected capability.</summary>
public interface ISecretResolutionLease : IAsyncDisposable
{
    /// <summary>Gets the stable non-secret reference identity.</summary>
    ProgramKitIdentifier ReferenceIdentity { get; }

    /// <summary>Gets the finite result capability kind.</summary>
    SecretResultKind ResultKind { get; }

    /// <summary>Gets safe lifecycle metadata.</summary>
    SecretLifecycleMetadata Lifecycle { get; }
}
