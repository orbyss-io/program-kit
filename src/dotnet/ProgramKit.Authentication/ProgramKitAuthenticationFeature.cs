using CShells;
using CShells.Features;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Options;

namespace ProgramKit.Authentication;

/// <summary>Composes profile-independent authentication and permission services into a shell.</summary>
[ShellFeature(
    name: "ProgramKit.Authentication",
    DisplayName = "Program Kit Authentication",
    Description = "Provides validated authentication configuration and canonical permission policies.")]
public sealed class ProgramKitAuthenticationFeature(ShellSettings settings) : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        services.Configure<ProgramKitWebOptions>(
            settings.GetConfigurationRoot().GetSection(ProgramKitWebOptions.SectionName));
        services.AddSingleton<IValidateOptions<ProgramKitWebOptions>, ProgramKitWebOptionsValidator>();
        services.AddAuthorizationBuilder().SetFallbackPolicy(
            new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build());
        services.AddTransient<IClaimsTransformation, PermissionClaimsTransformation>();
        services.AddSingleton<IAuthorizationPolicyProvider, PermissionPolicyProvider>();
        services.TryAddSingleton<IAuthenticationErrorWriter, DefaultAuthenticationErrorWriter>();
    }
}
