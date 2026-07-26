using System.Globalization;
using System.Text;
using Orbyss.ProgramKit.DotNet.Operations.Security;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Deterministic .NET 10 OIDC, JWT bearer, and operation-policy compiler.</summary>
public sealed class DotNetSecurityProjectionCompiler : IDotNetSecurityProjectionCompiler
{
    /// <inheritdoc />
    public ImmutableArray<GeneratedOutput> Compile(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        if (host.Security is null)
        {
            return [];
        }

        var outputs = ImmutableArray.CreateBuilder<GeneratedOutput>();
        outputs.Add(Output(
            "ProgramKitOperationAuthorizationMiddleware",
            RenderOperationAuthorizationMiddleware(host.Security)));
        outputs.Add(Output(
            "ProgramKitSecurityPolicyStartupValidator",
            RenderPolicyStartupValidator(host.Security)));
        if (host.Security.OidcConfidentialInteractive?.ClientAuthentication.Method ==
            DotNetOidcClientAuthenticationMethod.PrivateKeyJwtAssertion)
        {
            outputs.Add(Output(
                "IProgramKitOidcClientAssertionProvider",
                RenderAssertionProvider()));
            outputs.Add(Output(
                "ProgramKitOidcClientAssertion",
                RenderAssertion()));
        }

        if (host.Security.OidcPublicBrowser is { } publicBrowser)
        {
            outputs.AddRange(RenderPublicBrowser(publicBrowser));
        }

        return outputs.ToImmutable();
    }

    /// <inheritdoc />
    public string RenderRegistration(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        if (host.Security is null)
        {
            return string.Empty;
        }

        var security = host.Security;
        var builder = new StringBuilder();
        builder.AppendLine("var programKitAuthentication = builder.Services.AddAuthentication(options =>");
        builder.AppendLine("{");
        builder.Append("    options.DefaultAuthenticateScheme = ")
            .Append(Literal(security.Defaults.AuthenticateScheme)).AppendLine(";");
        builder.Append("    options.DefaultChallengeScheme = ")
            .Append(Literal(security.Defaults.ChallengeScheme)).AppendLine(";");
        builder.Append("    options.DefaultForbidScheme = ")
            .Append(Literal(security.Defaults.ForbidScheme)).AppendLine(";");
        if (security.Defaults.SignInScheme is not null)
        {
            builder.Append("    options.DefaultSignInScheme = ")
                .Append(Literal(security.Defaults.SignInScheme)).AppendLine(";");
        }

        if (security.Defaults.SignOutScheme is not null)
        {
            builder.Append("    options.DefaultSignOutScheme = ")
                .Append(Literal(security.Defaults.SignOutScheme)).AppendLine(";");
        }

        builder.AppendLine("});");
        if (security.OidcConfidentialInteractive is { } oidc)
        {
            RenderOidcRegistration(builder, oidc);
        }

        if (security.JwtResourceServer is { } jwt)
        {
            RenderJwtRegistration(builder, jwt);
        }

        if (security.OidcPublicBrowser is { } publicBrowser)
        {
            RenderPublicBrowserCorsRegistration(builder, publicBrowser);
        }

        builder.AppendLine("var programKitAuthorization = builder.Services.AddAuthorizationBuilder();");
        foreach (var policy in security.Policies
                     .Where(static item =>
                         item.RegistrationOwnership ==
                         DotNetPolicyRegistrationOwnership.ProgramKitAuthenticatedTransport)
                     .OrderBy(static item => item.PolicyName, StringComparer.Ordinal))
        {
            builder.Append("programKitAuthorization.AddPolicy(")
                .Append(Literal(policy.PolicyName)).AppendLine(", policy =>");
            builder.AppendLine("{");
            builder.Append("    policy.AddAuthenticationSchemes(")
                .Append(string.Join(
                    ", ",
                    policy.AuthenticationSchemes
                        .Order(StringComparer.Ordinal)
                        .Select(Literal)))
                .AppendLine(");");
            builder.AppendLine("    policy.RequireAuthenticatedUser();");
            builder.AppendLine("});");
        }

        builder.AppendLine("builder.Services.AddHostedService<global::GeneratedHost.Hosting.ProgramKitSecurityPolicyStartupValidator>();");
        builder.AppendLine("builder.Services.AddTransient<global::GeneratedHost.Hosting.ProgramKitOperationAuthorizationMiddleware>();");
        return builder.ToString();
    }

    /// <inheritdoc />
    public string RenderMiddleware(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        if (host.Security is null)
        {
            return string.Empty;
        }

        var builder = new StringBuilder();
        if (host.Security.OidcPublicBrowser is { } publicBrowser)
        {
            builder.Append("app.UseCors(")
                .Append(Literal(publicBrowser.CorsPolicyName))
                .AppendLine(");");
        }

        builder.AppendLine("app.UseAuthentication();");
        builder.AppendLine("app.UseAuthorization();");
        builder.AppendLine("app.UseMiddleware<global::GeneratedHost.Hosting.ProgramKitOperationAuthorizationMiddleware>();");
        return builder.ToString();
    }

    private static void RenderPublicBrowserCorsRegistration(
        StringBuilder builder,
        DotNetOidcPublicBrowserProfile profile)
    {
        builder.AppendLine("builder.Services.AddCors(options =>");
        builder.AppendLine("{");
        builder.Append("    options.AddPolicy(")
            .Append(Literal(profile.CorsPolicyName))
            .AppendLine(", policy =>");
        builder.AppendLine("    {");
        builder.Append("        policy.WithOrigins(")
            .Append(string.Join(
                ", ",
                profile.CorsAllowedOrigins
                    .Select(static uri => uri.GetLeftPart(UriPartial.Authority))
                    .Order(StringComparer.Ordinal)
                    .Select(Literal)))
            .AppendLine(");");
        builder.Append("        policy.WithMethods(")
            .Append(string.Join(
                ", ",
                profile.CorsAllowedMethods
                    .Order(StringComparer.Ordinal)
                    .Select(Literal)))
            .AppendLine(");");
        builder.AppendLine("        policy.WithHeaders(\"Authorization\", \"Content-Type\");");
        builder.AppendLine("        policy.DisallowCredentials();");
        builder.AppendLine("    });");
        builder.AppendLine("});");
    }

    private static ImmutableArray<GeneratedOutput> RenderPublicBrowser(
        DotNetOidcPublicBrowserProfile profile) =>
        [
            DirectOutput(
                "PublicBrowser/PublicBrowser.csproj",
                RenderPublicBrowserProject(profile)),
            DirectOutput(
                "PublicBrowser/Program.cs",
                RenderPublicBrowserProgram(profile)),
            DirectOutput(
                "PublicBrowser/App.razor",
                RenderPublicBrowserApp()),
            DirectOutput(
                "PublicBrowser/_Imports.razor",
                RenderPublicBrowserImports()),
            DirectOutput(
                "PublicBrowser/Pages/Authentication.razor",
                RenderPublicBrowserAuthenticationPage()),
            DirectOutput(
                "PublicBrowser/wwwroot/index.html",
                RenderPublicBrowserIndex()),
            DirectOutput(
                "PublicBrowserVerification/PublicBrowserVerification.csproj",
                RenderPublicBrowserVerificationProject()),
            DirectOutput(
                "PublicBrowserVerification/ProgramKitGenerated/Operations/PublicBrowserProtocolVectors.cs",
                RenderPublicBrowserProtocolVectors(profile)),
            DirectOutput(
                "PublicBrowserVerification/ProgramKitGenerated/Operations/PublicBrowserPlaywrightHarness.cs",
                RenderPublicBrowserPlaywrightHarness(profile)),
            DirectOutput(
                "PublicBrowserVerification/ProgramKitGenerated/Operations/OperatorAssistedPublicBrowserAcceptance.cs",
                RenderOperatorAssistedAcceptance(profile)),
            DirectOutput(
                "PublicBrowserVerification/chromium.runsettings",
                RenderBrowserRunSettings("chromium")),
            DirectOutput(
                "PublicBrowserVerification/firefox.runsettings",
                RenderBrowserRunSettings("firefox")),
            DirectOutput(
                "PublicBrowserVerification/webkit.runsettings",
                RenderBrowserRunSettings("webkit")),
            DirectOutput(
                "PublicBrowserVerification/.gitignore",
                """
                playwright/.auth/
                playwright-report/
                test-results/
                traces/
                *.zip
                """),
        ];

    private static string RenderPublicBrowserProject(
        DotNetOidcPublicBrowserProfile profile)
    {
        var builder = new StringBuilder();
        builder.AppendLine("<Project Sdk=\"Microsoft.NET.Sdk.BlazorWebAssembly\">");
        builder.AppendLine("  <PropertyGroup>");
        builder.AppendLine("    <OutputType>Exe</OutputType>");
        builder.AppendLine("    <TargetFramework>net10.0</TargetFramework>");
        builder.AppendLine("    <LangVersion>14.0</LangVersion>");
        builder.AppendLine("    <Nullable>enable</Nullable>");
        builder.AppendLine("    <ImplicitUsings>enable</ImplicitUsings>");
        builder.AppendLine("    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>");
        builder.AppendLine("    <RootNamespace>GeneratedPublicBrowser</RootNamespace>");
        builder.AppendLine("  </PropertyGroup>");
        builder.AppendLine("  <ItemGroup>");
        foreach (var package in profile.TargetAdapter.Packages
                     .OrderBy(static item => item.PackageId, StringComparer.Ordinal))
        {
            builder.Append("    <PackageReference Include=\"")
                .Append(DotNetSourceText.Xml(package.PackageId))
                .Append("\" Version=\"[")
                .Append(DotNetSourceText.Xml(package.Version.Value))
                .AppendLine("]\" />");
        }

        builder.AppendLine("  </ItemGroup>");
        builder.AppendLine("</Project>");
        return builder.ToString();
    }

    private static string RenderPublicBrowserProgram(
        DotNetOidcPublicBrowserProfile profile)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("using Microsoft.AspNetCore.Components.Web;");
        builder.AppendLine("using Microsoft.AspNetCore.Components.WebAssembly.Authentication;");
        builder.AppendLine("using Microsoft.AspNetCore.Components.WebAssembly.Hosting;");
        builder.AppendLine("using Microsoft.AspNetCore.Components;");
        builder.AppendLine();
        builder.AppendLine("var builder = WebAssemblyHostBuilder.CreateDefault(args);");
        builder.AppendLine("builder.RootComponents.Add<GeneratedPublicBrowser.App>(\"#app\");");
        builder.AppendLine("builder.RootComponents.Add<HeadOutlet>(\"head::after\");");
        builder.AppendLine("builder.Services.AddOidcAuthentication(options =>");
        builder.AppendLine("{");
        builder.Append("    options.ProviderOptions.Authority = ")
            .Append(Literal(profile.Authority.AbsoluteUri)).AppendLine(";");
        builder.Append("    options.ProviderOptions.ClientId = ")
            .Append(Literal(profile.ClientId)).AppendLine(";");
        builder.AppendLine("    options.ProviderOptions.ResponseType = \"code\";");
        builder.Append("    options.ProviderOptions.RedirectUri = ")
            .Append(Literal(profile.RedirectUri.AbsoluteUri)).AppendLine(";");
        builder.Append("    options.ProviderOptions.PostLogoutRedirectUri = ")
            .Append(Literal(profile.PostLogoutRedirectUri.AbsoluteUri)).AppendLine(";");
        builder.AppendLine("    options.ProviderOptions.DefaultScopes.Clear();");
        foreach (var scope in profile.Scopes.Order(StringComparer.Ordinal))
        {
            builder.Append("    options.ProviderOptions.DefaultScopes.Add(")
                .Append(Literal(scope)).AppendLine(");");
        }

        builder.AppendLine("});");
        builder.AppendLine("builder.Services.AddScoped(sp =>");
        builder.AppendLine("{");
        builder.AppendLine("    var authorization = new AuthorizationMessageHandler(");
        builder.AppendLine("        sp.GetRequiredService<IAccessTokenProvider>(),");
        builder.AppendLine("        sp.GetRequiredService<NavigationManager>())");
        builder.Append("        .ConfigureHandler([")
            .Append(Literal(profile.ApiResource.AbsoluteUri.TrimEnd('/')))
            .Append("], [")
            .Append(string.Join(
                ", ",
                profile.Scopes
                    .Where(static scope => scope is not ("openid" or "profile"))
                    .Order(StringComparer.Ordinal)
                    .Select(Literal)))
            .AppendLine("]);");
        builder.AppendLine("    authorization.InnerHandler = new HttpClientHandler();");
        builder.Append("    return new HttpClient(authorization) { BaseAddress = new Uri(")
            .Append(Literal(profile.ApiResource.AbsoluteUri)).AppendLine(") };");
        builder.AppendLine("});");
        builder.AppendLine("await builder.Build().RunAsync();");
        return builder.ToString();
    }

    private static string RenderPublicBrowserApp() =>
        """
        @* <auto-generated program-kit> *@
        <CascadingAuthenticationState>
            <Router AppAssembly="@typeof(App).Assembly">
                <Found Context="routeData">
                    <AuthorizeRouteView RouteData="@routeData" />
                </Found>
                <NotFound>
                    <p role="status">Not found.</p>
                </NotFound>
            </Router>
        </CascadingAuthenticationState>
        """;

    private static string RenderPublicBrowserImports() =>
        """
        @using Microsoft.AspNetCore.Components.Authorization
        @using Microsoft.AspNetCore.Components.Routing
        @using Microsoft.AspNetCore.Components.WebAssembly.Authentication
        """;

    private static string RenderPublicBrowserAuthenticationPage() =>
        """
        @page "/authentication/{action}"
        @using Microsoft.AspNetCore.Components.WebAssembly.Authentication
        <RemoteAuthenticatorView Action="@Action" />

        @code {
            [Parameter]
            public string? Action { get; set; }
        }
        """;

    private static string RenderPublicBrowserIndex() =>
        """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Generated public browser</title>
        </head>
        <body>
          <div id="app">Loading...</div>
          <script src="_content/Microsoft.AspNetCore.Components.WebAssembly.Authentication/AuthenticationService.js"></script>
          <script src="_framework/blazor.webassembly.js"></script>
        </body>
        </html>
        """;

    private static string RenderPublicBrowserVerificationProject() =>
        """
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <LangVersion>14.0</LangVersion>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <RootNamespace>GeneratedPublicBrowser</RootNamespace>
          </PropertyGroup>
          <ItemGroup>
            <PackageReference Include="Microsoft.Playwright" Version="[1.61.0]" />
          </ItemGroup>
        </Project>
        """;

    private static string RenderBrowserRunSettings(string browser) =>
        string.Concat(
            """
            <?xml version="1.0" encoding="utf-8"?>
            <RunSettings>
              <Playwright>
                <BrowserName>
            """,
            browser,
            """
            </BrowserName>
              </Playwright>
            </RunSettings>
            """);

    private static string RenderPublicBrowserProtocolVectors(
        DotNetOidcPublicBrowserProfile profile)
    {
        var builder = VerificationSource("System.Security.Cryptography", "System.Text");
        builder.AppendLine("internal static class PublicBrowserProtocolVectors");
        builder.AppendLine("{");
        builder.Append("    internal static readonly Uri Authority = new(")
            .Append(Literal(profile.Authority.AbsoluteUri)).AppendLine(");");
        builder.Append("    internal static readonly Uri RedirectUri = new(")
            .Append(Literal(profile.RedirectUri.AbsoluteUri)).AppendLine(");");
        builder.Append("    internal static readonly Uri PostLogoutRedirectUri = new(")
            .Append(Literal(profile.PostLogoutRedirectUri.AbsoluteUri)).AppendLine(");");
        builder.Append("    internal static readonly Uri ApiResource = new(")
            .Append(Literal(profile.ApiResource.AbsoluteUri)).AppendLine(");");
        builder.Append("    internal static readonly Uri ExpectedIssuer = new(")
            .Append(Literal(profile.Authority.AbsoluteUri)).AppendLine(");");
        builder.AppendLine("    internal const bool RefreshTokenExpected = false;");
        builder.AppendLine("    internal static string CreateS256Challenge(string verifier)");
        builder.AppendLine("    {");
        builder.AppendLine("        ArgumentException.ThrowIfNullOrWhiteSpace(verifier);");
        builder.AppendLine("        return Convert.ToBase64String(SHA256.HashData(Encoding.ASCII.GetBytes(verifier)))");
        builder.AppendLine("            .TrimEnd('=').Replace('+', '-').Replace('/', '_');");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    internal static bool IsSafeCallback(Uri callback) =>");
        builder.AppendLine("        callback == RedirectUri &&");
        builder.AppendLine("        callback.Query.Length == 0 &&");
        builder.AppendLine("        callback.Fragment.Length == 0;");
        builder.AppendLine();
        builder.AppendLine("    internal static bool IsSafeLogoutCallback(Uri callback) =>");
        builder.AppendLine("        callback == PostLogoutRedirectUri &&");
        builder.AppendLine("        callback.Query.Length == 0 &&");
        builder.AppendLine("        callback.Fragment.Length == 0;");
        builder.AppendLine();
        builder.AppendLine("    internal static bool IsSafeAuthorizationResponse(");
        builder.AppendLine("        Uri callback,");
        builder.AppendLine("        Uri issuer,");
        builder.AppendLine("        string expectedState,");
        builder.AppendLine("        string actualState,");
        builder.AppendLine("        string expectedNonce,");
        builder.AppendLine("        string actualNonce) =>");
        builder.AppendLine("        IsSafeCallback(callback) &&");
        builder.AppendLine("        issuer == ExpectedIssuer &&");
        builder.AppendLine("        !string.IsNullOrEmpty(expectedState) &&");
        builder.AppendLine("        string.Equals(expectedState, actualState, StringComparison.Ordinal) &&");
        builder.AppendLine("        !string.IsNullOrEmpty(expectedNonce) &&");
        builder.AppendLine("        string.Equals(expectedNonce, actualNonce, StringComparison.Ordinal);");
        builder.AppendLine();
        builder.AppendLine("    internal static bool IsAllowedApiTarget(Uri target) =>");
        builder.AppendLine("        string.Equals(");
        builder.AppendLine("            target.GetLeftPart(UriPartial.Authority),");
        builder.AppendLine("            ApiResource.GetLeftPart(UriPartial.Authority),");
        builder.AppendLine("            StringComparison.Ordinal) &&");
        builder.AppendLine("        target.AbsolutePath.StartsWith(ApiResource.AbsolutePath, StringComparison.Ordinal);");
        builder.AppendLine();
        builder.AppendLine("    internal static bool IsAccessTokenKind(string tokenType, string? jwtType) =>");
        builder.AppendLine("        string.Equals(tokenType, \"Bearer\", StringComparison.Ordinal) &&");
        builder.AppendLine("        string.Equals(jwtType, \"at+jwt\", StringComparison.Ordinal);");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderPublicBrowserPlaywrightHarness(
        DotNetOidcPublicBrowserProfile profile)
    {
        var builder = VerificationSource("Microsoft.Playwright");
        builder.AppendLine("internal static class PublicBrowserPlaywrightHarness");
        builder.AppendLine("{");
        builder.AppendLine("    internal static async Task VerifyAsync(");
        builder.AppendLine("        string browserName,");
        builder.AppendLine("        Uri publicBrowserBaseUri,");
        builder.AppendLine("        Func<IPage, CancellationToken, Task> performLocalProviderLogin,");
        builder.AppendLine("        Func<IPage, CancellationToken, Task> assertProtectedApiAccess,");
        builder.AppendLine("        Func<IPage, CancellationToken, Task> assertAdversarialFailures,");
        builder.AppendLine("        CancellationToken cancellationToken)");
        builder.AppendLine("    {");
        builder.AppendLine("        cancellationToken.ThrowIfCancellationRequested();");
        builder.AppendLine("        using var playwright = await Playwright.CreateAsync();");
        builder.AppendLine("        var browserType = browserName switch");
        builder.AppendLine("        {");
        builder.AppendLine("            \"chromium\" => playwright.Chromium,");
        builder.AppendLine("            \"firefox\" => playwright.Firefox,");
        builder.AppendLine("            \"webkit\" => playwright.Webkit,");
        builder.AppendLine("            _ => throw new ArgumentOutOfRangeException(nameof(browserName)),");
        builder.AppendLine("        };");
        builder.AppendLine("        await using var browser = await browserType.LaunchAsync(new() { Headless = true });");
        builder.AppendLine("        await using var context = await browser.NewContextAsync(new()");
        builder.AppendLine("        {");
        builder.AppendLine("            BaseURL = publicBrowserBaseUri.AbsoluteUri,");
        builder.AppendLine("            RecordHarPath = null,");
        builder.AppendLine("            RecordVideoDir = null,");
        builder.AppendLine("        });");
        builder.AppendLine("        var page = await context.NewPageAsync();");
        builder.AppendLine("        page.Request += (_, request) =>");
        builder.AppendLine("        {");
        builder.AppendLine("            if (request.Url.Contains(\"access_token=\", StringComparison.OrdinalIgnoreCase) ||");
        builder.AppendLine("                request.Url.Contains(\"id_token=\", StringComparison.OrdinalIgnoreCase))");
        builder.AppendLine("                throw new InvalidOperationException(\"A token entered a browser URL.\");");
        builder.AppendLine("        };");
        builder.AppendLine("        await page.GotoAsync(publicBrowserBaseUri.AbsoluteUri);");
        builder.AppendLine("        await performLocalProviderLogin(page, cancellationToken);");
        builder.AppendLine("        await assertProtectedApiAccess(page, cancellationToken);");
        builder.AppendLine("        await assertAdversarialFailures(page, cancellationToken);");
        builder.AppendLine("        var localStorageCount = await page.EvaluateAsync<int>(\"() => window.localStorage.length\");");
        builder.AppendLine("        if (localStorageCount != 0)");
        builder.AppendLine("            throw new InvalidOperationException(\"Authentication material entered durable local storage.\");");
        builder.AppendLine("        await page.GotoAsync(new Uri(publicBrowserBaseUri, \"authentication/logout\").AbsoluteUri);");
        builder.AppendLine("        await context.ClearCookiesAsync();");
        builder.AppendLine("    }");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderOperatorAssistedAcceptance(
        DotNetOidcPublicBrowserProfile profile)
    {
        var builder = VerificationSource("Microsoft.Playwright");
        builder.AppendLine("internal static class OperatorAssistedPublicBrowserAcceptance");
        builder.AppendLine("{");
        builder.AppendLine("    internal static async Task RunOptInAsync(");
        builder.AppendLine("        Uri publicBrowserBaseUri,");
        builder.AppendLine("        Func<CancellationToken, Task> waitForHumanControlledCallback,");
        builder.AppendLine("        CancellationToken cancellationToken)");
        builder.AppendLine("    {");
        builder.AppendLine("        using var playwright = await Playwright.CreateAsync();");
        builder.AppendLine("        await using var browser = await playwright.Chromium.LaunchAsync(new() { Headless = false });");
        builder.AppendLine("        await using var context = await browser.NewContextAsync();");
        builder.AppendLine("        var page = await context.NewPageAsync();");
        builder.AppendLine("        await page.GotoAsync(new Uri(publicBrowserBaseUri, \"authentication/login\").AbsoluteUri);");
        builder.AppendLine("        await waitForHumanControlledCallback(cancellationToken);");
        builder.Append("        await page.WaitForURLAsync(")
            .Append(Literal(profile.RedirectUri.AbsoluteUri)).AppendLine(");");
        builder.AppendLine("        await context.ClearCookiesAsync();");
        builder.AppendLine("    }");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static StringBuilder VerificationSource(params string[] namespaces)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        foreach (var item in namespaces)
        {
            builder.Append("using ").Append(item).AppendLine(";");
        }

        builder.AppendLine();
        builder.AppendLine("namespace GeneratedPublicBrowser.Operations;");
        builder.AppendLine();
        return builder;
    }

    private static GeneratedOutput DirectOutput(string path, string content) =>
        new(path, DotNetSourceText.Utf8(content));

    private static void RenderOidcRegistration(
        StringBuilder builder,
        DotNetOidcConfidentialInteractiveProfile profile)
    {
        builder.Append("programKitAuthentication.AddCookie(")
            .Append(Literal(profile.CookieScheme)).AppendLine(", options =>");
        builder.AppendLine("{");
        RenderCookie(builder, "options.Cookie", profile.Cookie);
        builder.Append("    options.ExpireTimeSpan = TimeSpan.FromMinutes(")
            .Append(profile.Cookie.LifetimeMinutes.ToString(CultureInfo.InvariantCulture))
            .AppendLine(");");
        builder.AppendLine("    options.SlidingExpiration = false;");
        builder.AppendLine("});");
        builder.Append("programKitAuthentication.AddOpenIdConnect(")
            .Append(Literal(profile.Scheme)).AppendLine(", options =>");
        builder.AppendLine("{");
        builder.Append("    options.SignInScheme = ")
            .Append(Literal(profile.CookieScheme)).AppendLine(";");
        builder.Append("    options.Authority = ")
            .Append(Literal(profile.Authority.AbsoluteUri)).AppendLine(";");
        builder.Append("    options.MetadataAddress = ")
            .Append(Literal(profile.MetadataAddress.AbsoluteUri)).AppendLine(";");
        builder.Append("    options.ClientId = ")
            .Append(Literal(profile.ClientId)).AppendLine(";");
        builder.AppendLine("    options.ResponseType = global::Microsoft.IdentityModel.Protocols.OpenIdConnect.OpenIdConnectResponseType.Code;");
        builder.AppendLine("    options.ResponseMode = global::Microsoft.IdentityModel.Protocols.OpenIdConnect.OpenIdConnectResponseMode.FormPost;");
        builder.Append("    options.CallbackPath = ")
            .Append(Literal(profile.CallbackPath)).AppendLine(";");
        builder.Append("    options.SignedOutCallbackPath = ")
            .Append(Literal(profile.SignedOutCallbackPath)).AppendLine(";");
        builder.Append("    options.RemoteSignOutPath = ")
            .Append(Literal(profile.RemoteSignOutPath)).AppendLine(";");
        builder.AppendLine("    options.RequireHttpsMetadata = true;");
        builder.AppendLine("    options.UsePkce = true;");
        builder.AppendLine("    options.MapInboundClaims = false;");
        builder.AppendLine("    options.SaveTokens = false;");
        builder.AppendLine("    options.GetClaimsFromUserInfoEndpoint = false;");
        builder.AppendLine("    options.DisableTelemetry = true;");
        builder.Append("    options.RemoteAuthenticationTimeout = TimeSpan.FromSeconds(")
            .Append(profile.RemoteAuthenticationTimeoutSeconds.ToString(CultureInfo.InvariantCulture))
            .AppendLine(");");
        builder.AppendLine("    options.ProtocolValidator.RequireNonce = true;");
        builder.AppendLine("    options.ProtocolValidator.RequireStateValidation = true;");
        builder.Append("    options.PushedAuthorizationBehavior = ")
            .Append(profile.PushedAuthorization switch
            {
                DotNetOidcPushedAuthorizationBehavior.Require =>
                    "global::Microsoft.AspNetCore.Authentication.OpenIdConnect.PushedAuthorizationBehavior.Require",
                DotNetOidcPushedAuthorizationBehavior.UseIfAvailable =>
                    "global::Microsoft.AspNetCore.Authentication.OpenIdConnect.PushedAuthorizationBehavior.UseIfAvailable",
                _ =>
                    "global::Microsoft.AspNetCore.Authentication.OpenIdConnect.PushedAuthorizationBehavior.Disable",
            })
            .AppendLine(";");
        builder.AppendLine("    options.Scope.Clear();");
        foreach (var scope in profile.Scopes.Order(StringComparer.Ordinal))
        {
            builder.Append("    options.Scope.Add(").Append(Literal(scope)).AppendLine(");");
        }

        builder.AppendLine("    options.TokenValidationParameters = new global::Microsoft.IdentityModel.Tokens.TokenValidationParameters");
        builder.AppendLine("    {");
        builder.AppendLine("        ValidateIssuer = true,");
        builder.AppendLine("        ValidateAudience = true,");
        builder.AppendLine("        ValidateIssuerSigningKey = true,");
        builder.AppendLine("        ValidateLifetime = true,");
        builder.Append("        ValidAudience = ").Append(Literal(profile.ClientId)).AppendLine(",");
        builder.Append("        ValidAlgorithms = [")
            .Append(string.Join(
                ", ",
                profile.AllowedIdTokenAlgorithms.Order(StringComparer.Ordinal).Select(Literal)))
            .AppendLine("],");
        builder.AppendLine("    };");
        RenderCookie(builder, "options.CorrelationCookie", profile.CorrelationCookie);
        RenderCookie(builder, "options.NonceCookie", profile.NonceCookie);
        if (profile.ClientAuthentication.Method ==
            DotNetOidcClientAuthenticationMethod.ClientSecretPost)
        {
            builder.Append("    options.ClientSecret = builder.Configuration[")
                .Append(Literal(profile.ClientAuthentication.ConfigurationKey!))
                .Append("] ?? throw new InvalidOperationException(")
                .Append(Literal("The configured OIDC client-secret reference did not resolve."))
                .AppendLine(");");
        }
        else
        {
            builder.AppendLine("    options.Events.OnAuthorizationCodeReceived = async context =>");
            builder.AppendLine("    {");
            builder.AppendLine("        var provider = context.HttpContext.RequestServices");
            builder.AppendLine("            .GetRequiredService<global::GeneratedHost.Hosting.IProgramKitOidcClientAssertionProvider>();");
            builder.Append("        var assertion = await provider.CreateAsync(")
                .Append(Literal(profile.ClientAuthentication.Reference.Identity.Value))
                .AppendLine(", context.HttpContext.RequestAborted);");
            builder.AppendLine("        if (string.IsNullOrEmpty(assertion.Value) || assertion.ExpiresAt <= DateTimeOffset.UtcNow)");
            builder.AppendLine("        {");
            builder.AppendLine("            throw new InvalidOperationException(\"The OIDC client assertion is empty or expired.\");");
            builder.AppendLine("        }");
            builder.AppendLine("        var tokenEndpointRequest = context.TokenEndpointRequest ??");
            builder.AppendLine("            throw new InvalidOperationException(\"The OIDC token endpoint request is unavailable.\");");
            builder.AppendLine("        tokenEndpointRequest.ClientAssertion = assertion.Value;");
            builder.AppendLine("        tokenEndpointRequest.ClientAssertionType =");
            builder.AppendLine("            \"urn:ietf:params:oauth:client-assertion-type:jwt-bearer\";");
            builder.AppendLine("    };");
        }

        builder.AppendLine("});");
    }

    private static void RenderJwtRegistration(
        StringBuilder builder,
        DotNetJwtResourceServerProfile profile)
    {
        builder.Append("programKitAuthentication.AddJwtBearer(")
            .Append(Literal(profile.Scheme)).AppendLine(", options =>");
        builder.AppendLine("{");
        builder.Append("    options.Authority = ")
            .Append(Literal(profile.Authority.AbsoluteUri)).AppendLine(";");
        builder.Append("    options.MetadataAddress = ")
            .Append(Literal(profile.MetadataAddress.AbsoluteUri)).AppendLine(";");
        builder.Append("    options.Audience = ")
            .Append(Literal(profile.Audience)).AppendLine(";");
        builder.AppendLine("    options.RequireHttpsMetadata = true;");
        builder.AppendLine("    options.MapInboundClaims = false;");
        builder.AppendLine("    options.SaveToken = false;");
        builder.AppendLine("    options.TokenValidationParameters = new global::Microsoft.IdentityModel.Tokens.TokenValidationParameters");
        builder.AppendLine("    {");
        builder.AppendLine("        ValidateIssuerSigningKey = true,");
        builder.AppendLine("        RequireSignedTokens = true,");
        builder.AppendLine("        ValidateIssuer = true,");
        builder.Append("        ValidIssuer = ").Append(Literal(profile.Issuer)).AppendLine(",");
        builder.AppendLine("        ValidateAudience = true,");
        builder.Append("        ValidAudience = ").Append(Literal(profile.Audience)).AppendLine(",");
        builder.AppendLine("        ValidateLifetime = true,");
        builder.AppendLine("        RequireExpirationTime = true,");
        builder.Append("        ClockSkew = TimeSpan.FromSeconds(")
            .Append(profile.ClockSkewSeconds.ToString(CultureInfo.InvariantCulture))
            .AppendLine("),");
        builder.Append("        ValidAlgorithms = [")
            .Append(string.Join(
                ", ",
                profile.AllowedAlgorithms.Order(StringComparer.Ordinal).Select(Literal)))
            .AppendLine("],");
        builder.AppendLine("        ValidTypes = [\"at+jwt\"],");
        builder.AppendLine("    };");
        builder.AppendLine("});");
    }

    private static void RenderCookie(
        StringBuilder builder,
        string target,
        DotNetCookieSecurityProfile profile)
    {
        builder.Append("    ").Append(target).Append(".Name = ")
            .Append(Literal(profile.Name)).AppendLine(";");
        builder.Append("    ").Append(target)
            .AppendLine(".HttpOnly = true;");
        builder.Append("    ").Append(target)
            .AppendLine(".SecurePolicy = global::Microsoft.AspNetCore.Http.CookieSecurePolicy.Always;");
        builder.Append("    ").Append(target).Append(".SameSite = ")
            .Append(profile.SameSite == DotNetCookieSameSite.Lax
                ? "global::Microsoft.AspNetCore.Http.SameSiteMode.Lax"
                : "global::Microsoft.AspNetCore.Http.SameSiteMode.None")
            .AppendLine(";");
        builder.Append("    ").Append(target)
            .AppendLine(".IsEssential = false;");
    }

    private static string RenderOperationAuthorizationMiddleware(
        DotNetSecurityConfiguration security)
    {
        var builder = Source(
            "Microsoft.AspNetCore.Authentication",
            "Microsoft.AspNetCore.Authorization",
            "Microsoft.AspNetCore.Http",
            "Microsoft.AspNetCore.Routing",
            "Microsoft.AspNetCore.Routing.Template",
            "Microsoft.Extensions.DependencyInjection");
        builder.AppendLine("internal sealed class ProgramKitOperationAuthorizationMiddleware : IMiddleware");
        builder.AppendLine("{");
        builder.AppendLine("    public async Task InvokeAsync(HttpContext context, RequestDelegate next)");
        builder.AppendLine("    {");
        builder.AppendLine("        var authorization = context.RequestServices");
        builder.AppendLine("            .GetRequiredService<IAuthorizationService>();");
        foreach (var binding in security.OperationBindings
                     .OrderBy(static item => item.Path, StringComparer.Ordinal)
                     .ThenBy(static item => item.Method, StringComparer.Ordinal))
        {
            builder.Append("        if (HttpMethods.Is")
                .Append(MethodSuffix(binding.Method))
                .Append("(context.Request.Method) && Match(")
                .Append(Literal(binding.Path)).AppendLine(", context.Request.Path))");
            builder.AppendLine("        {");
            if (binding.Disposition == DotNetOperationSecurityDisposition.Anonymous)
            {
                builder.AppendLine("            await next(context);");
                builder.AppendLine("            return;");
            }
            else
            {
                var policy = security.Policies.Single(
                    item => item.PolicyRevision.Identity == binding.PolicyIdentity);
                builder.Append("            var result = await authorization.AuthorizeAsync(context.User, context, ")
                    .Append(Literal(policy.PolicyName)).AppendLine(");");
                builder.AppendLine("            if (result.Succeeded)");
                builder.AppendLine("            {");
                builder.AppendLine("                await next(context);");
                builder.AppendLine("                return;");
                builder.AppendLine("            }");
                builder.AppendLine("            if (context.User.Identity?.IsAuthenticated == true)");
                builder.AppendLine("            {");
                foreach (var scheme in policy.AuthenticationSchemes.Order(StringComparer.Ordinal))
                {
                    builder.Append("                await context.ForbidAsync(")
                        .Append(Literal(scheme)).AppendLine(");");
                }

                builder.AppendLine("            }");
                builder.AppendLine("            else");
                builder.AppendLine("            {");
                foreach (var scheme in policy.AuthenticationSchemes.Order(StringComparer.Ordinal))
                {
                    builder.Append("                await context.ChallengeAsync(")
                        .Append(Literal(scheme)).AppendLine(");");
                }

                builder.AppendLine("            }");
                builder.AppendLine("            return;");
            }

            builder.AppendLine("        }");
        }

        builder.AppendLine("        await next(context);");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    private static bool Match(string template, PathString path)");
        builder.AppendLine("    {");
        builder.AppendLine("        var matcher = new TemplateMatcher(TemplateParser.Parse(template), new RouteValueDictionary());");
        builder.AppendLine("        return matcher.TryMatch(path, new RouteValueDictionary());");
        builder.AppendLine("    }");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderPolicyStartupValidator(
        DotNetSecurityConfiguration security)
    {
        var builder = Source(
            "Microsoft.AspNetCore.Authorization",
            "Microsoft.Extensions.Hosting");
        builder.AppendLine("internal sealed class ProgramKitSecurityPolicyStartupValidator : IHostedService");
        builder.AppendLine("{");
        builder.AppendLine("    private readonly IAuthorizationPolicyProvider _provider;");
        builder.AppendLine();
        builder.AppendLine("    public ProgramKitSecurityPolicyStartupValidator(IAuthorizationPolicyProvider provider) => _provider = provider;");
        builder.AppendLine();
        builder.AppendLine("    public async Task StartAsync(CancellationToken cancellationToken)");
        builder.AppendLine("    {");
        foreach (var policy in security.Policies.OrderBy(static item => item.PolicyName, StringComparer.Ordinal))
        {
            builder.Append("        if (await _provider.GetPolicyAsync(")
                .Append(Literal(policy.PolicyName)).AppendLine(") is null)");
            builder.AppendLine("        {");
            builder.Append("            throw new InvalidOperationException(")
                .Append(Literal(string.Concat(
                    "Required authorization policy is not registered: ",
                    policy.PolicyName)))
                .AppendLine(");");
            builder.AppendLine("        }");
        }

        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderAssertionProvider()
    {
        var builder = Source();
        builder.AppendLine("internal interface IProgramKitOidcClientAssertionProvider");
        builder.AppendLine("{");
        builder.AppendLine("    ValueTask<ProgramKitOidcClientAssertion> CreateAsync(");
        builder.AppendLine("        string referenceIdentity,");
        builder.AppendLine("        CancellationToken cancellationToken);");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderAssertion()
    {
        var builder = Source();
        builder.AppendLine("internal sealed record ProgramKitOidcClientAssertion(");
        builder.AppendLine("    string Value,");
        builder.AppendLine("    DateTimeOffset ExpiresAt);");
        return builder.ToString();
    }

    private static GeneratedOutput Output(string typeName, string source) =>
        new(
            string.Concat("ProgramKitGenerated/Hosting/", typeName, ".cs"),
            DotNetSourceText.Utf8(source));

    private static StringBuilder Source(params string[] namespaces)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        foreach (var item in namespaces)
        {
            builder.Append("using ").Append(item).AppendLine(";");
        }

        builder.AppendLine();
        builder.AppendLine("namespace GeneratedHost.Hosting;");
        builder.AppendLine();
        return builder;
    }

    private static string MethodSuffix(string method) =>
        method.ToUpperInvariant() switch
        {
            "GET" => "Get",
            "POST" => "Post",
            "PUT" => "Put",
            "PATCH" => "Patch",
            "DELETE" => "Delete",
            "HEAD" => "Head",
            "OPTIONS" => "Options",
            "TRACE" => "Trace",
            _ => throw new InvalidOperationException(
                string.Concat("Unsupported operation method: ", method)),
        };

    private static string Literal(string value) =>
        DotNetSourceText.CSharpLiteral(value);
}
