using Microsoft.Extensions.Options;

namespace ProgramKit.Host.Web;

/// <summary>Rejects incomplete or unsafe selected-profile configuration during startup.</summary>
internal sealed class ProgramKitWebOptionsValidator(IHostEnvironment environment)
    : IValidateOptions<ProgramKitWebOptions>
{
    /// <inheritdoc />
    public ValidateOptionsResult Validate(string? name, ProgramKitWebOptions options)
    {
        if (options.Profile == ProgramKitWebProfile.None)
        {
            return ValidateOptionsResult.Success;
        }

        var failures = new List<string>();
        Require(options.Authority, "ProgramKit:Web:Authority", failures);
        Require(options.ClientId, "ProgramKit:Web:ClientId", failures);
        Require(options.Audience, "ProgramKit:Web:Audience", failures);
        Require(options.RoleClaim, "ProgramKit:Web:RoleClaim", failures);
        Require(options.PermissionClaim, "ProgramKit:Web:PermissionClaim", failures);
        if (options.Profile == ProgramKitWebProfile.BffCookie)
        {
            Require(options.ClientSecret, "ProgramKit:Web:ClientSecret", failures);
        }

        if (Uri.TryCreate(options.Authority, UriKind.Absolute, out var authority))
        {
            var localHttpAllowed = environment.IsDevelopment()
                && options.AllowHttpForLocalDevelopment
                && authority.Scheme == Uri.UriSchemeHttp
                && (authority.IsLoopback || authority.Host.Equals("keycloak", StringComparison.OrdinalIgnoreCase));
            if (authority.Scheme != Uri.UriSchemeHttps && !localHttpAllowed)
            {
                failures.Add("ProgramKit:Web:Authority must use HTTPS; local HTTP requires the explicit development override.");
            }
        }
        else
        {
            failures.Add("ProgramKit:Web:Authority must be an absolute URI.");
        }

        if (options.Scopes.Length == 0 || !options.Scopes.Contains("openid", StringComparer.Ordinal))
        {
            failures.Add("ProgramKit:Web:Scopes must include openid.");
        }

        if (options.Profile == ProgramKitWebProfile.SpaPkce && options.AllowedOrigins.Length == 0)
        {
            failures.Add("ProgramKit:Web:AllowedOrigins must contain at least one exact origin for SpaPkce.");
        }

        foreach (var origin in options.AllowedOrigins)
        {
            if (origin.Contains('*', StringComparison.Ordinal)
                || !Uri.TryCreate(origin, UriKind.Absolute, out var parsed)
                || parsed.AbsolutePath != "/"
                || !string.IsNullOrEmpty(parsed.Query)
                || !string.IsNullOrEmpty(parsed.Fragment))
            {
                failures.Add($"ProgramKit:Web:AllowedOrigins contains an invalid or non-exact origin: {origin}");
            }
        }

        ValidatePath(options.CallbackPath, "CallbackPath", failures);
        ValidatePath(options.SignedOutCallbackPath, "SignedOutCallbackPath", failures);
        ValidatePath(options.RemoteSignOutPath, "RemoteSignOutPath", failures);
        ValidatePath(options.AccessDeniedPath, "AccessDeniedPath", failures);
        if (options.SupportedLocales.Length == 0
            || !options.SupportedLocales.Contains(options.DefaultLocale, StringComparer.OrdinalIgnoreCase))
        {
            failures.Add("ProgramKit:Web:SupportedLocales must contain ProgramKit:Web:DefaultLocale.");
        }

        foreach (var locale in options.SupportedLocales)
        {
            try
            {
                _ = System.Globalization.CultureInfo.GetCultureInfo(locale);
            }
            catch (System.Globalization.CultureNotFoundException)
            {
                failures.Add($"ProgramKit:Web:SupportedLocales contains an unknown locale: {locale}");
            }
        }

        if (options.DiscoveryTimeoutSeconds is < 1 or > 30)
        {
            failures.Add("ProgramKit:Web:DiscoveryTimeoutSeconds must be between 1 and 30.");
        }

        if (options.SessionIdleMinutes < 1 || options.SessionAbsoluteMinutes < options.SessionIdleMinutes)
        {
            failures.Add("ProgramKit:Web session lifetime must be positive and absolute lifetime must not be shorter than idle lifetime.");
        }

        ValidatePermissionMappings(options.RolePermissions, "RolePermissions", failures);
        ValidatePermissionMappings(options.ScopePermissions, "ScopePermissions", failures);

        return failures.Count == 0 ? ValidateOptionsResult.Success : ValidateOptionsResult.Fail(failures);
    }

    /// <summary>Adds a required-value failure for an empty setting.</summary>
    private static void Require(string value, string path, ICollection<string> failures)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            failures.Add($"{path} is required by the selected secure web profile.");
        }
    }

    /// <summary>Adds a failure when a protocol callback is not a local absolute path.</summary>
    private static void ValidatePath(string value, string name, ICollection<string> failures)
    {
        if (!value.StartsWith("/", StringComparison.Ordinal) || value.StartsWith("//", StringComparison.Ordinal))
        {
            failures.Add($"ProgramKit:Web:{name} must be a local absolute path.");
        }
    }

    /// <summary>Rejects empty provider keys and permission identities.</summary>
    private static void ValidatePermissionMappings(
        IReadOnlyDictionary<string, string[]> mappings,
        string name,
        ICollection<string> failures)
    {
        foreach (var (source, permissions) in mappings)
        {
            if (string.IsNullOrWhiteSpace(source)
                || permissions.Length == 0
                || permissions.Any(string.IsNullOrWhiteSpace))
            {
                failures.Add(
                    $"ProgramKit:Web:{name} must map a non-empty provider value to non-empty application permissions.");
            }
        }
    }
}
