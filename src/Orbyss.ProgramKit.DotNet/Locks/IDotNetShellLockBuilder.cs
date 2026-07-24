using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Builds deterministic exact host locks from a validated shell.</summary>
public interface IDotNetShellLockBuilder
{
    /// <summary>Builds a lock for all hosts in deterministic identity order.</summary>
    DotNetShellLockDocument Build(
        DotNetShellDocument shell,
        ArtifactReference shellRevision);
}
