using CShells.Lifecycle;

namespace ProgramKit.Examples.CShellsInitializerOwnership;

/// <summary>Awaits admission without taking disposal ownership of the injected resource.</summary>
public sealed class ResourceAdmission(SyntheticResourceOwner owner) : IShellInitializer
{
    /// <inheritdoc />
    public Task InitializeAsync(CancellationToken cancellationToken = default) =>
        owner.AdmitAsync(cancellationToken);
}
