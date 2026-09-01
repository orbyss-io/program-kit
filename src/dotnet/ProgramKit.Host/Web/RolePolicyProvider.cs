using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.Options;

namespace ProgramKit.Host.Web;

/// <summary>Builds authenticated role policies from stable <c>role:name</c> policy identifiers.</summary>
internal sealed class RolePolicyProvider(IOptions<AuthorizationOptions> options)
    : DefaultAuthorizationPolicyProvider(options)
{
    /// <summary>Prefixes role-backed dynamic policies.</summary>
    private const string Prefix = "role:";

    /// <inheritdoc />
    public override Task<AuthorizationPolicy?> GetPolicyAsync(string policyName)
    {
        if (!policyName.StartsWith(Prefix, StringComparison.OrdinalIgnoreCase))
        {
            return base.GetPolicyAsync(policyName);
        }

        var role = policyName[Prefix.Length..].Trim();
        if (role.Length == 0)
        {
            return Task.FromResult<AuthorizationPolicy?>(null);
        }

        var policy = new AuthorizationPolicyBuilder()
            .RequireAuthenticatedUser()
            .RequireRole(role)
            .Build();
        return Task.FromResult<AuthorizationPolicy?>(policy);
    }
}
