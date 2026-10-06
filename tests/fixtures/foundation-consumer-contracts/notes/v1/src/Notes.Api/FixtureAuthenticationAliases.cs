using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;
using Microsoft.Extensions.DependencyInjection;

namespace Notes.Api;

// Deterministic fixture instrumentation, not domain admission. The signed issuer
// supplies ordinary userinfo aliases; native claim actions must leave Foundation's
// validated reserved issuer/subject projection intact. A raw-claim owner mutant
// therefore cannot accidentally pass merely because its aliases happen to agree.
internal static class FixtureAuthenticationAliases
{
    internal static void Register(IServiceCollection services) =>
        services.PostConfigure<OpenIdConnectOptions>(OpenIdConnectDefaults.AuthenticationScheme, options =>
        {
            options.ClaimActions.DeleteClaim("iss");
            options.ClaimActions.DeleteClaim("sub");
            options.ClaimActions.MapJsonKey("iss", "fixture_raw_issuer");
            options.ClaimActions.MapJsonKey("sub", "fixture_raw_subject");
        });
}
