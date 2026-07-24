using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.DotNet.Locks;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Verifies an isolated restore lock against exact local and external selections.</summary>
public interface INuGetLockVerifier
{
    /// <summary>Fails unless every restored package is exact, allowed, and hash-bound.</summary>
    void Verify(
        ReadOnlyMemory<byte> lockBytes,
        LocalPackageRootManifest packageManifest,
        DotNetHostLock hostLock);
}
