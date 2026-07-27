using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Fail-closed exact host-lock selector.</summary>
public sealed class DotNetHostLockSelector : IDotNetHostLockSelector
{
    /// <inheritdoc />
    public DotNetHostLock Resolve(
        DotNetShellLockDocument document,
        ProgramKitIdentifier hostIdentity,
        DotNetHostKind requiredKind)
    {
        ArgumentNullException.ThrowIfNull(document);
        var matches = document.HostLocks.IsDefault
            ? []
            : document.HostLocks
                .Where(candidate =>
                    string.Equals(
                        candidate.HostIdentity.Value,
                        hostIdentity.Value,
                        StringComparison.Ordinal))
                .ToArray();
        if (matches.Length != 1 || matches[0].Kind != requiredKind)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidHostSelection,
                "The requested host must resolve to exactly one lock with the required generator kind.",
                "/hostLocks");
        }

        return matches[0];
    }
}
