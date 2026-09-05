using System.Security.Claims;
using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using ProgramKit.Authentication;
using ProgramKit.WebDefaults;

namespace ProgramKit.Authentication.BffCookie;

/// <summary>Composes the confidential OIDC BFF-cookie profile into one shell.</summary>
[ShellFeature(
    name: "ProgramKit.Authentication.BffCookie",
    DisplayName = "Program Kit BFF Cookie Authentication",
    Description = "Provides server-held OIDC tokens, an opaque session cookie, antiforgery, and BFF endpoints.",
    DependsOn = [typeof(ProgramKitAuthenticationFeature), typeof(ProgramKitWebDefaultsFeature)])]
public sealed class ProgramKitBffCookieFeature : IWebShellFeature, IMiddlewareShellFeature
{
    /// <summary>Names the accepted antiforgery header.</summary>
    public const string AntiforgeryHeader = "X-CSRF-TOKEN";

    /// <summary>Names the accepted antiforgery form field.</summary>
    public const string AntiforgeryFormField = "__RequestVerificationToken";

    /// <inheritdoc />
    public int Order => -800;

    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<IProgramKitAuthenticationProfile, BffCookieProfileMarker>();
        services.AddSingleton<IValidateOptions<ProgramKitWebOptions>, BffCookieOptionsValidator>();
        services.AddAuthentication(options =>
            {
                options.DefaultAuthenticateScheme = CookieAuthenticationDefaults.AuthenticationScheme;
                options.DefaultSignInScheme = CookieAuthenticationDefaults.AuthenticationScheme;
                options.DefaultChallengeScheme = OpenIdConnectDefaults.AuthenticationScheme;
            })
            .AddCookie(_ => { })
            .AddOpenIdConnect(_ => { });
        services.AddDistributedMemoryCache();
        services.AddSingleton<ITicketStore, DistributedTicketStore>();
        ConfigureCookie(services);
        ConfigureOpenIdConnect(services);
        ConfigureAntiforgery(services);
    }

    /// <inheritdoc />
    public void UseMiddleware(IApplicationBuilder app, IHostEnvironment? environment)
    {
        app.UseAuthentication();
        app.UseMiddleware<AntiforgeryMiddleware>();
        app.UseAuthorization();
    }

    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        var selected = endpoints.ServiceProvider.GetRequiredService<IOptions<ProgramKitWebOptions>>().Value;
        endpoints.MapGet("/bff/login", (string? returnUrl) =>
        {
            var destination = IsLocalReturnUrl(returnUrl) ? returnUrl! : "/";
            return Results.Challenge(
                new AuthenticationProperties { RedirectUri = destination },
                [OpenIdConnectDefaults.AuthenticationScheme]);
        }).AllowAnonymous();

        endpoints.MapGet("/bff/user", WriteUserAsync).AllowAnonymous();

        endpoints.MapGet("/bff/antiforgery", (HttpContext context, IAntiforgery antiforgery) =>
        {
            var tokens = antiforgery.GetAndStoreTokens(context);
            return Results.Ok(new
            {
                headerName = AntiforgeryHeader,
                formFieldName = AntiforgeryFormField,
                requestToken = tokens.RequestToken
            });
        }).AllowAnonymous();

        endpoints.MapPost("/bff/logout", LogoutAsync).RequireAuthorization();
        endpoints.MapGet("/bff/signed-out", () => Results.Ok(new { signedOut = true })).AllowAnonymous();
        endpoints.MapGet(selected.AccessDeniedPath, WriteAccessDeniedAsync).AllowAnonymous();
    }

    /// <summary>Configures the opaque server-backed session cookie.</summary>
    private static void ConfigureCookie(IServiceCollection services)
    {
        services.AddOptions<CookieAuthenticationOptions>(CookieAuthenticationDefaults.AuthenticationScheme)
            .Configure<IOptions<ProgramKitWebOptions>, IHostEnvironment, ITicketStore>(
                (options, selected, environment, store) =>
                {
                    var settings = selected.Value;
                    var insecureLocal = environment.IsDevelopment() && settings.AllowHttpForLocalDevelopment;
                    options.SessionStore = store;
                    options.Cookie.Name = insecureLocal ? "program-kit-session-local" : settings.CookieName;
                    options.Cookie.HttpOnly = true;
                    options.Cookie.SameSite = SameSiteMode.Lax;
                    options.Cookie.SecurePolicy = insecureLocal
                        ? CookieSecurePolicy.SameAsRequest
                        : CookieSecurePolicy.Always;
                    options.Cookie.Path = "/";
                    options.SlidingExpiration = true;
                    options.ExpireTimeSpan = TimeSpan.FromMinutes(settings.SessionIdleMinutes);
                    options.AccessDeniedPath = settings.AccessDeniedPath;
                    options.Events.OnRedirectToLogin = context => ApiRedirectAsErrorAsync(
                        context,
                        StatusCodes.Status401Unauthorized,
                        "authentication_required");
                    options.Events.OnRedirectToAccessDenied = context => ApiRedirectAsErrorAsync(
                        context,
                        StatusCodes.Status403Forbidden,
                        "authorization_denied");
                });
    }

    /// <summary>Configures the confidential OIDC protocol handler.</summary>
    private static void ConfigureOpenIdConnect(IServiceCollection services)
    {
        services.AddOptions<OpenIdConnectOptions>(OpenIdConnectDefaults.AuthenticationScheme)
            .Configure<IOptions<ProgramKitWebOptions>, IHostEnvironment>((options, selected, environment) =>
            {
                var settings = selected.Value;
                options.Authority = settings.Authority;
                if (!string.IsNullOrWhiteSpace(settings.BackchannelAuthority))
                {
                    options.MetadataAddress =
                        $"{settings.BackchannelAuthority.TrimEnd('/')}/.well-known/openid-configuration";
                }
                options.ClientId = settings.ClientId;
                options.ClientSecret = settings.ClientSecret;
                options.ResponseType = "code";
                options.UsePkce = true;
                options.SaveTokens = true;
                options.GetClaimsFromUserInfoEndpoint = true;
                options.MapInboundClaims = false;
                options.RequireHttpsMetadata = !(environment.IsDevelopment() && settings.AllowHttpForLocalDevelopment);
                options.CallbackPath = settings.CallbackPath;
                options.SignedOutCallbackPath = settings.SignedOutCallbackPath;
                options.RemoteSignOutPath = settings.RemoteSignOutPath;
                options.RemoteAuthenticationTimeout = TimeSpan.FromSeconds(settings.RemoteAuthenticationTimeoutSeconds);
                options.BackchannelTimeout = TimeSpan.FromSeconds(settings.DiscoveryTimeoutSeconds);
                if (environment.IsDevelopment() && settings.AllowHttpForLocalDevelopment)
                {
                    options.CorrelationCookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
                    options.NonceCookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
                }

                options.Scope.Clear();
                foreach (var scope in settings.Scopes)
                {
                    options.Scope.Add(scope);
                }

                options.TokenValidationParameters = ValidationParameters(settings, settings.ClientId);
                options.Events.OnTokenValidated = context =>
                {
                    if (
                        string.IsNullOrWhiteSpace(context.Principal?.FindFirstValue("iss"))
                        || string.IsNullOrWhiteSpace(context.Principal?.FindFirstValue("sub")))
                    {
                        context.Fail("The validated OpenID Connect identity requires issuer and subject claims.");
                    }
                    return Task.CompletedTask;
                };
                options.Events.OnRemoteFailure = context =>
                {
                    var code = context.Failure is HttpRequestException or TaskCanceledException
                        ? "identity_provider_unavailable"
                        : "authentication_callback_invalid";
                    context.HandleResponse();
                    context.Response.Redirect($"{settings.AccessDeniedPath}?code={code}");
                    return Task.CompletedTask;
                };
            });
    }

    /// <summary>Configures the BFF antiforgery token transports and cookie.</summary>
    private static void ConfigureAntiforgery(IServiceCollection services)
    {
        services.AddAntiforgery();
        services.AddOptions<AntiforgeryOptions>()
            .Configure<IOptions<ProgramKitWebOptions>, IHostEnvironment>((options, selected, environment) =>
            {
                options.HeaderName = AntiforgeryHeader;
                options.FormFieldName = AntiforgeryFormField;
                var insecureLocal = environment.IsDevelopment() && selected.Value.AllowHttpForLocalDevelopment;
                options.Cookie.Name = insecureLocal
                    ? "program-kit-antiforgery-local"
                    : "__Host-program-kit-antiforgery";
                options.Cookie.HttpOnly = true;
                options.Cookie.SecurePolicy = insecureLocal
                    ? CookieSecurePolicy.SameAsRequest
                    : CookieSecurePolicy.Always;
                options.Cookie.SameSite = SameSiteMode.Strict;
            });
    }

    /// <summary>Clears the local session before attempting provider logout.</summary>
    private static async Task LogoutAsync(HttpContext context, ILoggerFactory loggerFactory)
    {
        await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme).ConfigureAwait(false);
        try
        {
            await context.SignOutAsync(
                OpenIdConnectDefaults.AuthenticationScheme,
                new AuthenticationProperties { RedirectUri = "/bff/signed-out" }).ConfigureAwait(false);
        }
        catch (Exception exception) when (
            exception is HttpRequestException or InvalidOperationException or TaskCanceledException)
        {
            loggerFactory.CreateLogger("ProgramKit.RemoteLogout")
                .LogWarning("Remote logout could not be initiated after the local session was cleared.");
            context.Response.Redirect("/bff/signed-out?remote=unavailable");
        }
    }

    /// <summary>Returns a minimal session projection only for a validated issuer-subject identity.</summary>
    private static async Task WriteUserAsync(
        HttpContext context,
        IOptions<ProgramKitWebOptions> options,
        IAuthenticationErrorWriter errorWriter)
    {
        var user = context.User;
        if (user.Identity?.IsAuthenticated != true)
        {
            await context.Response.WriteAsJsonAsync(new { authenticated = false }).ConfigureAwait(false);
            return;
        }

        var issuer = user.FindFirstValue("iss");
        var subject = user.FindFirstValue("sub");
        if (string.IsNullOrWhiteSpace(issuer) || string.IsNullOrWhiteSpace(subject))
        {
            await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme).ConfigureAwait(false);
            await errorWriter.WriteAsync(
                context,
                StatusCodes.Status401Unauthorized,
                "authentication_identity_invalid").ConfigureAwait(false);
            return;
        }

        var permissions = user.FindAll(options.Value.PermissionClaim).Select(claim => claim.Value)
            .Distinct(StringComparer.Ordinal).Order(StringComparer.Ordinal).ToArray();
        await context.Response.WriteAsJsonAsync(new
        {
            authenticated = true,
            issuer,
            subject,
            displayName = user.FindFirstValue("name"),
            permissions
        }).ConfigureAwait(false);
    }

    /// <summary>Maps interactive protocol failures to stable authentication error codes.</summary>
    private static Task WriteAccessDeniedAsync(
        HttpContext context,
        string? code,
        IAuthenticationErrorWriter errorWriter)
    {
        var (status, stableCode) = code switch
        {
            "authentication_callback_invalid" =>
                (StatusCodes.Status400BadRequest, "authentication_callback_invalid"),
            "identity_provider_unavailable" =>
                (StatusCodes.Status503ServiceUnavailable, "identity_provider_unavailable"),
            _ => (StatusCodes.Status403Forbidden, "authorization_denied")
        };
        return errorWriter.WriteAsync(context, status, stableCode);
    }

    /// <summary>Converts API cookie redirects into an authentication error response.</summary>
    private static Task ApiRedirectAsErrorAsync(
        RedirectContext<CookieAuthenticationOptions> context,
        int status,
        string code)
    {
        if (!context.Request.Path.StartsWithSegments("/api"))
        {
            context.Response.Redirect(context.RedirectUri);
            return Task.CompletedTask;
        }

        return context.HttpContext.RequestServices.GetRequiredService<IAuthenticationErrorWriter>()
            .WriteAsync(context.HttpContext, status, code);
    }

    /// <summary>Creates the issuer, audience, signing-key, and lifetime validation contract.</summary>
    private static TokenValidationParameters ValidationParameters(ProgramKitWebOptions selected, string audience) =>
        new()
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidAudience = audience,
            ValidateIssuerSigningKey = true,
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),
            NameClaimType = "name",
            RoleClaimType = selected.RoleClaim
        };

    /// <summary>Returns whether an interactive return target stays inside the application.</summary>
    private static bool IsLocalReturnUrl(string? value) => !string.IsNullOrWhiteSpace(value)
        && value.StartsWith("/", StringComparison.Ordinal)
        && !value.StartsWith("//", StringComparison.Ordinal)
        && !value.StartsWith("/\\", StringComparison.Ordinal);
}
