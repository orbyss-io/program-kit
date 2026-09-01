using System.Security.Claims;
using System.Globalization;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Localization;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

namespace ProgramKit.Host.Web;

/// <summary>Registers, orders, and maps the selected secure web boundary exactly once.</summary>
internal static class ProgramKitWebBoundary
{
    /// <summary>Names the exact-origin direct-SPA CORS policy.</summary>
    private const string CorsPolicy = "program-kit-spa";

    /// <summary>Registers selected-profile services and validates their configuration on startup.</summary>
    public static IServiceCollection AddProgramKitWebBoundary(
        this IServiceCollection services,
        IConfiguration configuration,
        IHostEnvironment environment)
    {
        var section = configuration.GetSection(ProgramKitWebOptions.SectionName);
        var selected = section.Get<ProgramKitWebOptions>() ?? new ProgramKitWebOptions();
        services.AddSingleton<IValidateOptions<ProgramKitWebOptions>, ProgramKitWebOptionsValidator>();
        services.AddOptions<ProgramKitWebOptions>().Bind(section).ValidateOnStart();
        services.AddProblemDetails(options => options.CustomizeProblemDetails = context =>
        {
            context.ProblemDetails.Extensions["code"] ??= CodeFor(context.HttpContext.Response.StatusCode);
            context.ProblemDetails.Extensions["traceId"] = context.HttpContext.TraceIdentifier;
        });
        services.AddOpenApi("v1");
        services.AddHttpClient("program-kit-identity-readiness").RemoveAllLoggers();
        services.AddLocalization();
        services.Configure<RequestLocalizationOptions>(options =>
        {
            var cultures = selected.SupportedLocales.Select(CultureInfo.GetCultureInfo).ToArray();
            options.DefaultRequestCulture = new RequestCulture(selected.DefaultLocale);
            options.SupportedCultures = cultures;
            options.SupportedUICultures = cultures;
            options.ApplyCurrentCultureToResponseHeaders = true;
        });
        services.AddSingleton<IdentityReadinessState>();
        services.AddHostedService<IdentityReadinessService>();

        if (selected.Profile == ProgramKitWebProfile.None)
        {
            return services;
        }

        services.AddAuthorizationBuilder().SetFallbackPolicy(
            new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build());
        services.AddSingleton<IAuthorizationPolicyProvider, RolePolicyProvider>();

        if (selected.Profile == ProgramKitWebProfile.BffCookie)
        {
            AddBffAuthentication(services, selected, environment);
            services.AddDistributedMemoryCache();
            services.AddSingleton<ITicketStore, DistributedTicketStore>();
            services.AddOptions<CookieAuthenticationOptions>(CookieAuthenticationDefaults.AuthenticationScheme)
                .Configure<ITicketStore>((options, store) => options.SessionStore = store);
            services.AddAntiforgery(options =>
            {
                options.HeaderName = "X-CSRF-TOKEN";
                var insecureLocal = environment.IsDevelopment() && selected.AllowHttpForLocalDevelopment;
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
        else
        {
            AddSpaAuthentication(services, selected);
            services.AddCors(options => options.AddPolicy(CorsPolicy, policy => policy
                .WithOrigins(selected.AllowedOrigins)
                .WithMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
                .WithHeaders("Authorization", "Content-Type", CorrelationAndSecurityHeadersMiddleware.HeaderName)
                .WithExposedHeaders(CorrelationAndSecurityHeadersMiddleware.HeaderName)
                .SetPreflightMaxAge(TimeSpan.FromMinutes(10))));
        }

        return services;
    }

    /// <summary>Adds the selected profile's security middleware in its required order.</summary>
    public static WebApplication UseProgramKitWebBoundary(this WebApplication app)
    {
        var options = app.Services.GetRequiredService<IOptions<ProgramKitWebOptions>>().Value;
        app.UseMiddleware<CorrelationAndSecurityHeadersMiddleware>();
        app.UseExceptionHandler();
        app.UseStatusCodePages(async statusContext =>
        {
            var response = statusContext.HttpContext.Response;
            await Results.Problem(
                statusCode: response.StatusCode,
                extensions: new Dictionary<string, object?>
                {
                    ["code"] = CodeFor(response.StatusCode),
                    ["traceId"] = statusContext.HttpContext.TraceIdentifier
                }).ExecuteAsync(statusContext.HttpContext).ConfigureAwait(false);
        });
        app.UseRequestLocalization();
        if (!app.Environment.IsDevelopment())
        {
            app.UseHsts();
        }

        if (options.Profile == ProgramKitWebProfile.None)
        {
            return app;
        }

        if (options.Profile == ProgramKitWebProfile.SpaPkce)
        {
            app.UseCors(CorsPolicy);
        }

        app.UseAuthentication();
        if (options.Profile == ProgramKitWebProfile.BffCookie)
        {
            app.Use(async (context, next) =>
            {
                if (IsUnsafe(context.Request.Method)
                    && (context.Request.Path.StartsWithSegments("/api")
                        || context.Request.Path.Equals("/bff/logout")))
                {
                    try
                    {
                        await context.RequestServices.GetRequiredService<IAntiforgery>()
                            .ValidateRequestAsync(context).ConfigureAwait(false);
                    }
                    catch (AntiforgeryValidationException)
                    {
                        await WriteProblemAsync(context, StatusCodes.Status400BadRequest, "invalid_antiforgery_token")
                            .ConfigureAwait(false);
                        return;
                    }
                }

                await next(context).ConfigureAwait(false);
            });
        }

        app.UseAuthorization();
        return app;
    }

    /// <summary>Maps the standard BFF session and protocol endpoints when that profile is selected.</summary>
    public static IEndpointRouteBuilder MapProgramKitWebBoundary(this IEndpointRouteBuilder endpoints)
    {
        var options = endpoints.ServiceProvider.GetRequiredService<IOptions<ProgramKitWebOptions>>().Value;
        if (options.Profile != ProgramKitWebProfile.BffCookie)
        {
            return endpoints;
        }

        endpoints.MapGet("/bff/login", (string? returnUrl) =>
        {
            var destination = IsLocalReturnUrl(returnUrl) ? returnUrl! : "/";
            return Results.Challenge(
                new AuthenticationProperties { RedirectUri = destination },
                [OpenIdConnectDefaults.AuthenticationScheme]);
        }).AllowAnonymous();

        endpoints.MapGet("/bff/user", (ClaimsPrincipal user) =>
        {
            if (user.Identity?.IsAuthenticated != true)
            {
                return Results.Ok(new { authenticated = false });
            }

            var roles = user.FindAll(ClaimTypes.Role).Select(claim => claim.Value)
                .Distinct(StringComparer.Ordinal).Order(StringComparer.Ordinal).ToArray();
            return Results.Ok(new
            {
                authenticated = true,
                subject = user.FindFirstValue("sub"),
                displayName = user.FindFirstValue("name"),
                roles
            });
        }).AllowAnonymous();

        endpoints.MapGet("/bff/antiforgery", (HttpContext context, IAntiforgery antiforgery) =>
        {
            var tokens = antiforgery.GetAndStoreTokens(context);
            return Results.Ok(new { headerName = "X-CSRF-TOKEN", requestToken = tokens.RequestToken });
        }).AllowAnonymous();

        endpoints.MapPost("/bff/logout", async (HttpContext context, ILoggerFactory loggerFactory) =>
        {
            await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme).ConfigureAwait(false);
            try
            {
                await context.SignOutAsync(
                    OpenIdConnectDefaults.AuthenticationScheme,
                    new AuthenticationProperties { RedirectUri = "/bff/signed-out" }).ConfigureAwait(false);
            }
            catch (Exception exception) when (exception is HttpRequestException or InvalidOperationException)
            {
                loggerFactory.CreateLogger("ProgramKit.RemoteLogout")
                    .LogWarning("Remote logout could not be initiated after the local session was cleared.");
                context.Response.Redirect("/bff/signed-out?remote=unavailable");
            }
        }).RequireAuthorization();

        endpoints.MapGet("/bff/signed-out", () => Results.Ok(new { signedOut = true })).AllowAnonymous();
        endpoints.MapGet(options.AccessDeniedPath, () =>
            Results.Problem(statusCode: StatusCodes.Status403Forbidden, extensions: new Dictionary<string, object?>
            {
                ["code"] = "authorization_denied"
            })).AllowAnonymous();

        return endpoints;
    }

    /// <summary>Configures confidential OIDC and the opaque server-backed session cookie.</summary>
    private static void AddBffAuthentication(
        IServiceCollection services,
        ProgramKitWebOptions selected,
        IHostEnvironment environment)
    {
        services.AddAuthentication(options =>
        {
            options.DefaultAuthenticateScheme = CookieAuthenticationDefaults.AuthenticationScheme;
            options.DefaultSignInScheme = CookieAuthenticationDefaults.AuthenticationScheme;
            options.DefaultChallengeScheme = OpenIdConnectDefaults.AuthenticationScheme;
        })
        .AddCookie(options =>
        {
            var insecureLocal = environment.IsDevelopment() && selected.AllowHttpForLocalDevelopment;
            options.Cookie.Name = insecureLocal ? "program-kit-session-local" : selected.CookieName;
            options.Cookie.HttpOnly = true;
            options.Cookie.SameSite = SameSiteMode.Lax;
            options.Cookie.SecurePolicy = insecureLocal
                ? CookieSecurePolicy.SameAsRequest
                : CookieSecurePolicy.Always;
            options.Cookie.Path = "/";
            options.SlidingExpiration = true;
            options.ExpireTimeSpan = TimeSpan.FromMinutes(selected.SessionIdleMinutes);
            options.AccessDeniedPath = selected.AccessDeniedPath;
            options.Events.OnRedirectToLogin = context => ApiRedirectAsProblem(context, StatusCodes.Status401Unauthorized, "authentication_required");
            options.Events.OnRedirectToAccessDenied = context => ApiRedirectAsProblem(context, StatusCodes.Status403Forbidden, "authorization_denied");
        })
        .AddOpenIdConnect(options =>
        {
            options.Authority = selected.Authority;
            options.ClientId = selected.ClientId;
            options.ClientSecret = selected.ClientSecret;
            options.ResponseType = "code";
            options.UsePkce = true;
            options.SaveTokens = true;
            options.GetClaimsFromUserInfoEndpoint = true;
            options.MapInboundClaims = false;
            options.RequireHttpsMetadata = !(environment.IsDevelopment() && selected.AllowHttpForLocalDevelopment);
            options.CallbackPath = selected.CallbackPath;
            options.SignedOutCallbackPath = selected.SignedOutCallbackPath;
            options.RemoteSignOutPath = selected.RemoteSignOutPath;
            options.RemoteAuthenticationTimeout = TimeSpan.FromSeconds(selected.RemoteAuthenticationTimeoutSeconds);
            if (environment.IsDevelopment() && selected.AllowHttpForLocalDevelopment)
            {
                options.CorrelationCookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
                options.NonceCookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
            }
            options.Scope.Clear();
            foreach (var scope in selected.Scopes)
            {
                options.Scope.Add(scope);
            }

            options.TokenValidationParameters = ValidationParameters(selected, selected.ClientId);
        });
    }

    /// <summary>Configures API bearer validation for the explicit direct-SPA profile.</summary>
    private static void AddSpaAuthentication(IServiceCollection services, ProgramKitWebOptions selected)
    {
        services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(options =>
            {
                options.Authority = selected.Authority;
                options.Audience = selected.Audience;
                options.MapInboundClaims = false;
                options.RequireHttpsMetadata = !selected.AllowHttpForLocalDevelopment;
                options.TokenValidationParameters = ValidationParameters(selected, selected.Audience);
                options.Events = new JwtBearerEvents
                {
                    OnChallenge = async context =>
                    {
                        context.HandleResponse();
                        await WriteProblemAsync(context.HttpContext, StatusCodes.Status401Unauthorized, "authentication_required")
                            .ConfigureAwait(false);
                    },
                    OnForbidden = context => WriteProblemAsync(context.HttpContext, StatusCodes.Status403Forbidden, "authorization_denied")
                };
            });
    }

    /// <summary>Creates the common issuer, audience, lifetime, name, and role validation contract.</summary>
    private static TokenValidationParameters ValidationParameters(ProgramKitWebOptions selected, string audience) => new()
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

    /// <summary>Converts cookie redirects to stable API problems while preserving interactive redirects.</summary>
    private static Task ApiRedirectAsProblem(RedirectContext<CookieAuthenticationOptions> context, int status, string code)
    {
        if (!context.Request.Path.StartsWithSegments("/api"))
        {
            context.Response.Redirect(context.RedirectUri);
            return Task.CompletedTask;
        }

        return WriteProblemAsync(context.HttpContext, status, code);
    }

    /// <summary>Writes a stable authentication boundary Problem Details response.</summary>
    private static async Task WriteProblemAsync(HttpContext context, int status, string code)
    {
        context.Response.StatusCode = status;
        await Results.Problem(
            statusCode: status,
            extensions: new Dictionary<string, object?>
            {
                ["code"] = code,
                ["traceId"] = context.TraceIdentifier
            }).ExecuteAsync(context).ConfigureAwait(false);
    }

    /// <summary>Returns whether an HTTP method can mutate server state.</summary>
    private static bool IsUnsafe(string method) => !HttpMethods.IsGet(method)
        && !HttpMethods.IsHead(method)
        && !HttpMethods.IsOptions(method)
        && !HttpMethods.IsTrace(method);

    /// <summary>Returns whether a login return target is an application-local path.</summary>
    private static bool IsLocalReturnUrl(string? value) => !string.IsNullOrWhiteSpace(value)
        && value.StartsWith("/", StringComparison.Ordinal)
        && !value.StartsWith("//", StringComparison.Ordinal)
        && !value.StartsWith("/\\", StringComparison.Ordinal);

    /// <summary>Maps an HTTP status to the platform's default stable problem code.</summary>
    private static string CodeFor(int status) => status switch
    {
        StatusCodes.Status401Unauthorized => "authentication_required",
        StatusCodes.Status403Forbidden => "authorization_denied",
        StatusCodes.Status400BadRequest => "invalid_request",
        _ => "request_failed"
    };
}
