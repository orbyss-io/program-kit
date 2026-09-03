using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Options;

namespace ProgramKit.Host.Web;

/// <summary>Maps provider roles and scopes to deployment-owned canonical application permissions.</summary>
internal sealed class PermissionClaimsTransformation(IOptions<ProgramKitWebOptions> options)
    : IClaimsTransformation
{
    /// <inheritdoc />
    public Task<ClaimsPrincipal> TransformAsync(ClaimsPrincipal principal)
    {
        var settings = options.Value;
        var identity = principal.Identity as ClaimsIdentity;
        if (identity is null || !identity.IsAuthenticated)
            return Task.FromResult(principal);

        var permissions = new HashSet<string>(
            principal.FindAll(settings.PermissionClaim).Select(claim => claim.Value),
            StringComparer.Ordinal);
        AddMappedPermissions(
            principal.FindAll(settings.RoleClaim).Select(claim => claim.Value),
            settings.RolePermissions,
            permissions);
        AddMappedPermissions(
            principal.FindAll("scope").SelectMany(claim => claim.Value.Split(' ', StringSplitOptions.RemoveEmptyEntries)),
            settings.ScopePermissions,
            permissions);

        foreach (var permission in permissions)
        {
            if (!principal.HasClaim(settings.PermissionClaim, permission))
                identity.AddClaim(new Claim(settings.PermissionClaim, permission));
        }

        return Task.FromResult(principal);
    }

    /// <summary>Adds permissions mapped from provider-controlled values without wildcard expansion.</summary>
    /// <param name="values">The normalized provider values.</param>
    /// <param name="mappings">The exact deployment-owned mappings.</param>
    /// <param name="permissions">The canonical permission set to extend.</param>
    private static void AddMappedPermissions(
        IEnumerable<string> values,
        IReadOnlyDictionary<string, string[]> mappings,
        ISet<string> permissions)
    {
        foreach (var value in values)
        {
            if (!mappings.TryGetValue(value, out var mapped))
                continue;
            foreach (var permission in mapped)
                permissions.Add(permission);
        }
    }
}
