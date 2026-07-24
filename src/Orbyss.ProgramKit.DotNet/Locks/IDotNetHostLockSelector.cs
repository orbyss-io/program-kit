using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Selects exactly one host lock by exact identity and required generator kind.</summary>
public interface IDotNetHostLockSelector
{
    /// <summary>Returns the one compatible lock or fails closed.</summary>
    DotNetHostLock Resolve(
        DotNetShellLockDocument document,
        ProgramKitIdentifier hostIdentity,
        DotNetHostKind requiredKind);
}
