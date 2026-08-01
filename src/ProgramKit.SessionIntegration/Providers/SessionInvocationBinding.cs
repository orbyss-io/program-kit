using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.SessionIntegration.Providers;

public sealed record SessionInvocationBinding(
    string CanonicalInputFingerprint,
    string Operation,
    string WorkspaceIdentity,
    string ProviderIdentity,
    IReadOnlyList<string> Targets,
    string? GrantIdentity)
{
    public string BindingDigest => Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[]
    {
        CanonicalInputFingerprint,
        Operation,
        WorkspaceIdentity,
        ProviderIdentity,
        string.Join('\n', Targets.OrderBy(static value => value, StringComparer.Ordinal)),
        GrantIdentity ?? "no-grant",
    })));

    public static SessionInvocationBinding Create(
        string canonicalInputFingerprint,
        string operation,
        string workspaceIdentity,
        string providerIdentity,
        IReadOnlyList<string> targets,
        string? grantIdentity) => new(canonicalInputFingerprint, operation, workspaceIdentity, providerIdentity, targets.OrderBy(static value => value, StringComparer.Ordinal).ToArray(), grantIdentity);
}
