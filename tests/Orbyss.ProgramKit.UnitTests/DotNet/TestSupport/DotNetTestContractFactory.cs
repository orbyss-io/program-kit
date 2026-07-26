using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Documentation;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;
using Orbyss.ProgramKit.DotNet.Health;
using Orbyss.ProgramKit.DotNet.Operations;
using Orbyss.ProgramKit.DotNet.Operations.TransportFailures;
using Orbyss.ProgramKit.DotNet.Operations.Security;
using Orbyss.ProgramKit.DotNet.Observability;
using Orbyss.ProgramKit.DotNet.Packages;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Operations.Contracts;
using Orbyss.ProgramKit.Operations.Contracts.Transport;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

internal static class DotNetTestContractFactory
{
    internal static DotNetTransportFailureConfiguration TransportFailures()
    {
        var generic = new TransportFailureContract(
            Id("failure", "internal"),
            500,
            new Uri("https://errors.orbyss.test/internal"),
            "Unexpected failure",
            "The request could not be completed.",
            "The request failed in the local development host.",
            Ref("schema", "problem-details", 'a'),
            TransportFailureDisclosure.Public);
        var conflict = new TransportFailureContract(
            Id("failure", "conflict"),
            409,
            new Uri("https://errors.orbyss.test/conflict"),
            "Conflict",
            "The request conflicts with the current state.",
            "The declared operation conflict occurred.",
            Ref("schema", "problem-details", 'a'),
            TransportFailureDisclosure.Public);
        return new DotNetTransportFailureConfiguration(
            new TransportFailureProfile(
                Ref("profile", "transport-failures", 'b'),
                generic.Identity,
                [generic, conflict]),
            [new DotNetExceptionFailureMapping(
                10,
                "System.InvalidOperationException",
                conflict.Identity)],
            true,
            DotNetHandledExceptionDiagnostics.SuppressFrameworkAndEmitSanitizedOnce,
            DotNetResponseStartedDisposition.LeaveUnhandled,
            DotNetClientDisconnectDisposition.AbortWithoutResponse);
    }

    internal static DotNetShellDocument Shell()
    {
        var shellIdentity = Id("shell", "main");
        var featureIdentity = Id("feature", "sample");
        var activationIdentity = Id("activation", "sample");
        var operation = Ref("operation", "run", '1');
        var schema = Ref("schema", "run-result", '2');
        var feature = new DotNetFeatureSelection(
            featureIdentity,
            activationIdentity,
            shellIdentity,
            "Fixtures.SampleFeature",
            Package("Fixtures.SampleFeature", "1.0.0", '3'));
        var operationBinding = new DotNetOperationBinding(
            new OperationContractDescriptor(
                operation,
                [schema],
                [
                    new OperationResultContract(
                        schema,
                        OperationResultDisposition.Terminal),
                ],
                [schema],
                [],
                [
                    new RelatedOperationContract(
                        Id("relation", "additional-input"),
                        Ref("operation", "continue", '5'),
                        schema),
                ],
                null,
                null,
                OperationExpectedRevisionPolicy.Unsupported,
                OperationIdempotencyPolicy.Unsupported,
                OperationCancellationPolicy.Cooperative,
                OperationProgressPolicy.Unsupported,
                Compatibility(),
                new OperationDeprecation(false, null)),
            Ref("generator", "operation-projection", '4'));
        var healthListener = new DotNetHealthListener(
            Id("listener", "management"),
            "http",
            "127.0.0.1",
            18081,
            DotNetHealthExposure.Loopback,
            null,
            null,
            null);
        var livenessListener = new DotNetHealthListener(
            Id("listener", "liveness"),
            "http",
            "127.0.0.1",
            18082,
            DotNetHealthExposure.Loopback,
            null,
            null,
            null);
        var healthEndpoint = new DotNetHealthEndpoint(
            DotNetHealthEndpointKind.Readiness,
            "/health/ready",
            healthListener.Identity,
            ["ready"],
            [],
            new DotNetHealthStatusCodeMap(200, 200, 503),
            Ref("profile", "health-response", '6'),
            "no-store",
            Ref("policy", "health-authority", '7'),
            new DotNetHealthDocumentationSelection(
                DotNetHealthDocumentationDisposition.OwnedOperation,
                operation));
        var livenessEndpoint = new DotNetHealthEndpoint(
            DotNetHealthEndpointKind.Liveness,
            "/health/live",
            livenessListener.Identity,
            [],
            ["ready", "startup"],
            new DotNetHealthStatusCodeMap(200, 200, 503),
            Ref("profile", "health-response", '6'),
            "no-store",
            Ref("policy", "health-authority", '7'),
            new DotNetHealthDocumentationSelection(
                DotNetHealthDocumentationDisposition.Excluded,
                null));
        var jsonProvider = Provider(DotNetConfigurationProviderKind.JsonFile);
        var configurationSource = new DotNetConfigurationSource(
            Id("configuration-source", "appsettings"),
            0,
            DotNetConfigurationProviderKind.JsonFile,
            jsonProvider.ProviderRevision,
            jsonProvider.Package,
            "appsettings.json",
            null,
            [],
            null,
            false,
            DotNetConfigurationStartupDisposition.Required,
            new DotNetConfigurationReload(
                true,
                DotNetConfigurationReloadCapability.ChangeToken,
                null,
                null),
            DotNetConfigurationSecretClassification.PublicOnly,
            DotNetConfigurationFailureDisposition.Fail);
        var configurationDefinition = new DotNetConfigurationDefinition(
            Id("configuration", "sample-client"),
            new SemanticVersion("1.0.0"),
            Id("component", "sample-client"),
            DotNetConfigurationOwnerKind.External,
            "GeneratedHost.Configuration",
            "SampleClientOptions",
            "SampleClient",
            Ref("schema", "sample-client-configuration", '8'),
            [
                new DotNetConfigurationProperty(
                    "Endpoint",
                    "Endpoint",
                    DotNetConfigurationValueKind.AbsoluteUri,
                    true,
                    "https://localhost:7443",
                    "https://localhost:7443",
                    DotNetConfigurationValueClassification.Public,
                    new DotNetConfigurationPropertyValidation(
                        null,
                        null,
                        null,
                        null,
                        null)),
            ],
            Compatibility());
        var configurationBinding = new DotNetConfigurationBinding(
            configurationDefinition,
            string.Empty,
            [configurationSource.Identity],
            DotNetOptionsConsumption.Fixed,
            DotNetServiceLifetime.Singleton,
            true,
            false,
            DotNetConfigurationChangeReaction.None,
            false);
        var api = Host(
            "api",
            DotNetHostKind.Api,
            shellIdentity,
            activationIdentity,
            operationBinding,
            [
                Package("CShells", "0.0.28", '8'),
                Package("CShells.AspNetCore", "0.0.28", '9'),
                Package("Microsoft.Extensions.Configuration.Binder", "10.0.10", 'c'),
                Package("Microsoft.Extensions.Options", "10.0.10", 'b'),
                Package("Microsoft.Extensions.Options.ConfigurationExtensions", "10.0.10", 'e'),
                Package("Microsoft.Extensions.Options.DataAnnotations", "10.0.10", 'f'),
                Package("Microsoft.AspNetCore.Authentication.OpenIdConnect", "10.0.10", '7'),
                Package("Microsoft.AspNetCore.Authentication.JwtBearer", "10.0.10", '6'),
            ],
            configurationSource,
            configurationBinding,
            new DotNetHealthConfiguration(
                [healthEndpoint, livenessEndpoint],
                [healthListener, livenessListener]));
        var console = Host(
            "console",
            DotNetHostKind.Console,
            shellIdentity,
            activationIdentity,
            operationBinding,
            [
                Package("CShells", "0.0.28", '8'),
                Package("Microsoft.Extensions.Hosting", "10.0.10", 'a'),
                Package("Microsoft.Extensions.Configuration.Binder", "10.0.10", 'c'),
                Package("Microsoft.Extensions.Options", "10.0.10", 'b'),
                Package("Microsoft.Extensions.Options.ConfigurationExtensions", "10.0.10", 'e'),
                Package("Microsoft.Extensions.Options.DataAnnotations", "10.0.10", 'f'),
            ],
            configurationSource,
            configurationBinding,
            null);
        var worker = Host(
            "worker",
            DotNetHostKind.Worker,
            shellIdentity,
            activationIdentity,
            operationBinding,
            [
                Package("CShells", "0.0.28", '8'),
                Package("Microsoft.Extensions.Hosting", "10.0.10", 'a'),
                Package("Microsoft.Extensions.Configuration.Binder", "10.0.10", 'c'),
                Package("Microsoft.Extensions.Options", "10.0.10", 'b'),
                Package("Microsoft.Extensions.Options.ConfigurationExtensions", "10.0.10", 'e'),
                Package("Microsoft.Extensions.Options.DataAnnotations", "10.0.10", 'f'),
            ],
            configurationSource,
            configurationBinding,
            null);

        return new DotNetShellDocument(
            "pkid:schema:program-kit:dotnet-shell@9.0.0",
            new SemanticVersion("9.0.0"),
            Ref("version-map", "inputs", 'a'),
            Ref("version-selection", "inputs", 'b'),
            new DotNetShellComposition(
                "cshells",
                new SemanticVersion("0.0.28"),
                [new DotNetShellSelection(shellIdentity, ["sample"])]),
            [feature],
            new DotNetJsonSerializationSelection(
                [
                    new JsonSerializationProfileRef(
                        Id("profile", "contracts"),
                        new SemanticVersion("1.0.0"),
                        Digest('c')),
                ],
                []),
            [api, console, worker],
            Compatibility());
    }

    internal static OpenConsoleDocument ConsoleDocument(
        DotNetShellDocument shell)
    {
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Console);
        var operation = host.OperationBindings[0].OperationContract.OperationRevision;
        var schema = host.OperationBindings[0].GetResultSchemaRevisions()[0];
        var command = new OpenConsoleCommand(
            operation,
            ["observe", "run"],
            [["execute"], ["run-observation"]],
            "Runs the typed operation.",
            [
                new OpenConsoleArgument(
                    0,
                    "target",
                    "string",
                    new ConsoleValueArity(1, 1),
                    new ConsoleOccurrence(1, 1),
                    true,
                    null,
                    schema,
                    "Target identity."),
            ],
            [
                new OpenConsoleOption(
                    "count",
                    "c",
                    ["--number"],
                    ConsoleOptionKind.Value,
                    "int32",
                    new ConsoleValueArity(1, 1),
                    new ConsoleOccurrence(0, 1),
                    false,
                    "1",
                    schema,
                    "Observe:Count",
                    ["force"],
                    ["confirm"],
                    "Number of runs."),
                new OpenConsoleOption(
                    "force",
                    "f",
                    [],
                    ConsoleOptionKind.Flag,
                    "boolean",
                    new ConsoleValueArity(0, 0),
                    new ConsoleOccurrence(0, 1),
                    false,
                    null,
                    null,
                    null,
                    ["count"],
                    [],
                    "Forces execution."),
                new OpenConsoleOption(
                    "confirm",
                    null,
                    [],
                    ConsoleOptionKind.Flag,
                    "boolean",
                    new ConsoleValueArity(0, 0),
                    new ConsoleOccurrence(0, 1),
                    false,
                    null,
                    null,
                    null,
                    [],
                    [],
                    "Confirms execution."),
            ],
            null,
            new OpenConsoleStreamContract("stdout", "application/json", schema, true),
            new OpenConsoleStreamContract("stderr", "application/json", schema, false),
            [
                new OpenConsoleExitCode(0, "Succeeded", []),
                new OpenConsoleExitCode(2, "Invalid invocation", [schema]),
            ],
            Ref("policy", "run-authority", 'd'),
            [new OpenConsoleExample(["observe", "run", "target-1", "--count=2"], "Runs twice.")],
            null);
        return new OpenConsoleDocument(
            "pkid:schema:program-kit:open-console@1.0.0",
            new SemanticVersion("1.0.0"),
            new IntegratorDocumentInfo("sample", "Sample console.", new SemanticVersion("1.0.0")),
            Ref("host", "console", 'e'),
            new OpenConsoleParsing(true, "--", true, true, "invariant", "bounded-by-occurrence"),
            [],
            [command],
            new OpenConsoleHelp("help", "h", 0),
            new OpenConsoleCompletion("complete", true, true),
            Compatibility(),
            Provenance(host, operation));
    }

    internal static DotNetConfigurationProviderDescriptor Provider(
        DotNetConfigurationProviderKind kind) =>
        ProviderCatalog().Providers.Single(
            descriptor => descriptor.Kind == kind);

    internal static IDotNetConfigurationProviderCatalog ProviderCatalog()
    {
        DotNetConfigurationProviderComposition composition = new();
        return composition.CreateBuiltInCatalog();
    }

    internal static IDotNetConfigurationProviderGeneratorRegistry ProviderRegistry()
    {
        DotNetConfigurationProviderComposition composition = new();
        return composition.CreateBuiltInRegistry();
    }

    internal static OpenWorkerDocument WorkerDocument(
        DotNetShellDocument shell)
    {
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Worker);
        var operation = host.OperationBindings[0].OperationContract.OperationRevision;
        var feature = shell.Features[0];
        var schema = host.OperationBindings[0].GetResultSchemaRevisions()[0];
        var worker = new OpenWorkerEntry(
            operation,
            feature.FeatureIdentity,
            feature.ActivationIdentity,
            Ref("task-definition", "run", 'f'),
            "schedule",
            schema,
            [schema],
            [schema],
            [schema],
            Ref("policy", "worker-authority", '1'),
            Ref("policy", "worker-cancellation", '2'),
            null,
            Compatibility());
        return new OpenWorkerDocument(
            "pkid:schema:program-kit:open-worker@1.0.0",
            new SemanticVersion("1.0.0"),
            new IntegratorDocumentInfo("sample-worker", "Sample worker.", new SemanticVersion("1.0.0")),
            Ref("host", "worker", '3'),
            [worker],
            Compatibility(),
            Provenance(host, operation));
    }

    internal static OpenApiDocumentProjection ApiDocument(
        DotNetShellDocument shell)
    {
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Api);
        var binding = host.OperationBindings[0];
        return new OpenApiDocumentProjection(
            "Sample API",
            new SemanticVersion("1.0.0"),
            [new OpenApiServerProjection("https://localhost:8443", "Local API")],
            [
                new OpenApiOperationProjection(
                    "/runs",
                    "POST",
                    "run",
                    "Runs the operation.",
                    binding.OperationContract.OperationRevision,
                    binding.GetInputSchemaRevisions(),
                    binding.GetResultSchemaRevisions(),
                    binding.GetDiagnosticSchemaRevisions(),
                    binding.GetRelatedOperationRevisions(),
                    ProblemResponses(host),
                    new OpenApiOperationSecurityProjection(
                        false,
                        host.Security!.Policies[0].PolicyRevision.Identity,
                        host.Security.Policies[0].AuthenticationSchemes)),
            ],
            Provenance(host, binding.OperationContract.OperationRevision),
            SecuritySchemes(host));
    }

    internal static ArtifactReference Ref(
        string kind,
        string name,
        char digest) =>
        new(
            Id(kind, name),
            new SemanticVersion("1.0.0"),
            Digest(digest));

    internal static ProgramKitIdentifier Id(string kind, string name) =>
        new(string.Concat("pkid:", kind, ":test:", name));

    internal static Sha256Digest Digest(char value) =>
        new(string.Concat("sha256:", new string(value, 64)));

    private static DotNetHostDefinition Host(
        string name,
        DotNetHostKind kind,
        ProgramKitIdentifier shellIdentity,
        ProgramKitIdentifier activationIdentity,
        DotNetOperationBinding operation,
        ImmutableArray<DotNetPackageReference> packages,
        DotNetConfigurationSource configurationSource,
        DotNetConfigurationBinding configurationBinding,
        DotNetHealthConfiguration? health) =>
        new(
            Id("host", name),
            new SemanticVersion("1.0.0"),
            kind,
            Ref("profile", "dotnet-10", '4'),
            Ref("generator", string.Concat(name, "-host"), '5'),
            [shellIdentity],
            [activationIdentity],
            packages,
            [operation],
            [configurationSource],
            [configurationBinding],
            [],
            health,
            Compatibility(),
            Telemetry(name, kind),
            kind == DotNetHostKind.Api ? TransportFailures() : null,
            kind == DotNetHostKind.Api ? Security(operation) : null);

    internal static DotNetSecurityConfiguration Security(
        DotNetOperationBinding operation)
    {
        var policyRevision = Ref("policy", "authenticated-transport", '9');
        var jwtScheme = "ProgramKit.Jwt";
        var oidcScheme = "ProgramKit.Oidc";
        return new DotNetSecurityConfiguration(
            Ref("profile", "transport-security", '8'),
            new DotNetAuthenticationDefaults(
                jwtScheme,
                jwtScheme,
                jwtScheme,
                "ProgramKit.Cookie",
                oidcScheme),
            new DotNetOidcConfidentialInteractiveProfile(
                Ref("profile", "oidc-confidential-code-pkce", '7'),
                oidcScheme,
                "ProgramKit.Cookie",
                new Uri("https://identity.example.test/"),
                new Uri("https://identity.example.test/.well-known/openid-configuration"),
                "sample-confidential-client",
                new DotNetOidcClientAuthentication(
                    DotNetOidcClientAuthenticationMethod.ClientSecretPost,
                    new SecretReferenceDescriptor(
                        Id("secret-reference", "oidc-client"),
                        SecretReferenceClassification.RestrictedMetadata,
                        SecretResultKind.ConfigurationText,
                        Ref("capability", "configuration-secret-resolver", '4'),
                        Ref("locator", "oidc-client-secret", '5'),
                        SecretReferenceClassification.RestrictedMetadata),
                    "Authentication:Oidc:ClientSecret"),
                "/signin-oidc",
                "/signout-callback-oidc",
                "/signout-oidc",
                ["openid", "profile"],
                ["RS256", "PS256", "ES256"],
                DotNetOidcPushedAuthorizationBehavior.UseIfAvailable,
                DotNetTransportClaimMapping.PreserveProviderClaimNames,
                new DotNetCookieSecurityProfile(
                    "__Host-program-kit-session",
                    DotNetCookieSameSite.Lax,
                    true,
                    true,
                    false,
                    60),
                new DotNetCookieSecurityProfile(
                    "__Host-program-kit-correlation",
                    DotNetCookieSameSite.None,
                    true,
                    true,
                    false,
                    15),
                new DotNetCookieSecurityProfile(
                    "__Host-program-kit-nonce",
                    DotNetCookieSameSite.None,
                    true,
                    true,
                    false,
                    15),
                300,
                true,
                true,
                true,
                true,
                false,
                false),
            new DotNetOidcPublicBrowserProfile(
                Ref("profile", "oidc-public-browser-code-pkce", 'a'),
                DotNetPublicBrowserTargetAdapterCatalog.BlazorWebAssemblyOidc,
                new Uri("https://identity.example.test/"),
                new Uri("https://identity.example.test/.well-known/openid-configuration"),
                "sample-public-browser",
                new Uri("https://browser.example.test/authentication/login-callback"),
                new Uri("https://browser.example.test/authentication/logout-callback"),
                new Uri("https://browser.example.test/"),
                new Uri("https://api.example.test/"),
                "ProgramKit.PublicBrowser",
                [new Uri("https://browser.example.test/")],
                ["GET", "POST"],
                ["openid", "profile", "sample-api.read"],
                DotNetPublicBrowserTokenStorage.BrowserSession,
                DotNetPublicBrowserRefreshDisposition.Absent,
                Ref("acceptance", "public-browser-threat-model", 'b'),
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                new DotNetPublicBrowserVerification(
                    Ref("profile", "public-browser-verification", 'c'),
                    DotNetPublicBrowserTargetAdapterCatalog.Playwright,
                    [
                        DotNetBrowserEngine.Chromium,
                        DotNetBrowserEngine.Firefox,
                        DotNetBrowserEngine.WebKit,
                    ],
                    true,
                    true,
                    false,
                    false,
                    false,
                    true)),
            new DotNetJwtResourceServerProfile(
                Ref("profile", "oauth-jwt-resource-server", '6'),
                jwtScheme,
                new Uri("https://identity.example.test/"),
                new Uri("https://identity.example.test/.well-known/openid-configuration"),
                "https://identity.example.test/",
                "sample-api",
                ["RS256", "PS256", "ES256"],
                DotNetJwtAccessTokenProfile.Rfc9068AtJwt,
                DotNetTransportClaimMapping.PreserveProviderClaimNames,
                60,
                true,
                false),
            [
                new DotNetOAuthClientCredentialsProfile(
                    Ref("profile", "oauth-client-credentials", 'd'),
                    "catalog-service",
                    new Uri("https://identity.example.test/.well-known/oauth-authorization-server"),
                    new Uri("https://identity.example.test/connect/token"),
                    "catalog-client",
                    OAuthAuthentication("catalog-client"),
                    new Uri("https://catalog.example.test/"),
                    "catalog-api",
                    ["catalog.read"],
                    DotNetOAuthTokenType.AccessToken,
                    300,
                    30,
                    new DotNetOAuthCachePolicy(true, 30, 300),
                    true,
                    true,
                    true,
                    false,
                    false),
            ],
            [
                new DotNetOAuthTokenExchangeProfile(
                    Ref("profile", "oauth-token-exchange-rfc8693", 'e'),
                    "delegated-catalog-service",
                    new Uri("https://identity.example.test/.well-known/oauth-authorization-server"),
                    new Uri("https://identity.example.test/connect/token"),
                    "catalog-exchange-client",
                    OAuthAuthentication("catalog-exchange-client"),
                    new DotNetOAuthTokenSource(
                        Id("token-source", "explicit-subject"),
                        Ref("provenance", "explicit-subject-token", 'f'),
                        DotNetOAuthTokenType.AccessToken),
                    new DotNetOAuthTokenSource(
                        Id("token-source", "explicit-actor"),
                        Ref("provenance", "explicit-actor-token", '1'),
                        DotNetOAuthTokenType.Jwt),
                    DotNetOAuthExchangeMode.Delegation,
                    DotNetOAuthTokenType.AccessToken,
                    DotNetOAuthTokenType.AccessToken,
                    new Uri("https://catalog.example.test/"),
                    "catalog-api",
                    ["catalog.read"],
                    300,
                    30,
                    new DotNetOAuthCachePolicy(true, 30, 300),
                    true,
                    true,
                    true,
                    false,
                    false),
            ],
            [
                new DotNetNamedHostPolicyReference(
                    policyRevision,
                    "ProgramKit.AuthenticatedTransport",
                    [jwtScheme],
                    DotNetPolicyRegistrationOwnership.ProgramKitAuthenticatedTransport),
            ],
            [
                new DotNetOperationSecurityBinding(
                    operation.OperationContract.OperationRevision,
                    "POST",
                    "/runs",
                    DotNetOperationSecurityDisposition.NamedPolicy,
                    policyRevision.Identity),
            ]);
    }

    private static DotNetOAuthClientAuthentication OAuthAuthentication(string name) =>
        new(
            DotNetOAuthClientAuthenticationMethod.ClientSecretBasic,
            new SecretReferenceDescriptor(
                Id("secret-reference", name),
                SecretReferenceClassification.RestrictedMetadata,
                SecretResultKind.ConfigurationText,
                Ref("capability", "configuration-secret-resolver", '2'),
                Ref("locator", string.Concat(name, "-secret"), '3'),
                SecretReferenceClassification.RestrictedMetadata),
            string.Concat("Authentication:OAuth:", name, ":ClientSecret"));

    private static ImmutableArray<OpenApiSecuritySchemeProjection> SecuritySchemes(
        DotNetHostDefinition host)
    {
        if (host.Security is null)
        {
            return [];
        }

        return
        [
            new OpenApiSecuritySchemeProjection(
                host.Security.OidcConfidentialInteractive!.Scheme,
                OpenApiSecuritySchemeKind.OpenIdConnect,
                host.Security.OidcConfidentialInteractive.MetadataAddress,
                null),
            new OpenApiSecuritySchemeProjection(
                host.Security.JwtResourceServer!.Scheme,
                OpenApiSecuritySchemeKind.HttpBearerJwt,
                null,
                "JWT"),
        ];
    }

    private static ImmutableArray<OpenApiProblemDetailsResponseProjection> ProblemResponses(
        DotNetHostDefinition host) =>
        host.TransportFailures?.Profile.Failures.Select(static failure =>
            new OpenApiProblemDetailsResponseProjection(
                failure.StatusCode,
                failure.Identity,
                failure.Type,
                failure.Title,
                failure.ProblemSchemaRevision)).ToImmutableArray() ?? [];

    internal static DotNetTelemetryConfiguration Telemetry(
        string hostName = "api",
        DotNetHostKind kind = DotNetHostKind.Api) =>
        new(
            Ref("profile", "dotnet-telemetry", '1'),
            new ArtifactReference(
                Id("specification", "opentelemetry"),
                new SemanticVersion("1.55.0"),
                Digest('2')),
            new ArtifactReference(
                Id("semantic-convention", "opentelemetry-http"),
                new SemanticVersion("1.23.0"),
                Digest('3')),
            DotNetTelemetryPackageCatalog.Packages,
            new DotNetTelemetryResource(
                string.Concat("orbyss.test.", hostName),
                "orbyss.test",
                new SemanticVersion("1.0.0"),
                "test"),
            [
                new DotNetLoggerEvent(
                    "Orbyss.Test.Operations",
                    1001,
                    "OperationStarted",
                    DotNetLogLevel.Information,
                    "Operation {operationIdentity} started with correlation {correlationId}.",
                    ["operation.identity", "correlation.id"]),
            ],
            [
                new DotNetActivityDefinition(
                    "Orbyss.Test.Operations",
                    new SemanticVersion("1.0.0"),
                    "operation.execute",
                    DotNetActivityKind.Internal,
                    [
                        new DotNetTelemetryAttributeDefinition(
                            "operation.kind",
                            2,
                            ["command", "query"]),
                    ]),
            ],
            [
                new DotNetMetricDefinition(
                    "Orbyss.Test.Operations",
                    new SemanticVersion("1.0.0"),
                    "operation.duration",
                    DotNetMetricInstrumentKind.Histogram,
                    "s",
                    "Duration of one operation.",
                    [
                        new DotNetTelemetryAttributeDefinition(
                            "operation.outcome",
                            3,
                            ["succeeded", "failed", "cancelled"]),
                    ]),
            ],
            kind == DotNetHostKind.Api
                ?
                [
                    new DotNetTelemetryInstrumentation(
                        DotNetTelemetryInstrumentationKind.AspNetCore,
                        true,
                        true,
                        false),
                    new DotNetTelemetryInstrumentation(
                        DotNetTelemetryInstrumentationKind.HttpClient,
                        true,
                        true,
                        false),
                ]
                :
                [
                    new DotNetTelemetryInstrumentation(
                        DotNetTelemetryInstrumentationKind.HttpClient,
                        true,
                        true,
                        false),
                ],
            new DotNetTelemetrySampling(
                DotNetTelemetrySamplerKind.ParentBasedTraceIdRatio,
                1.0),
            new DotNetOtlpExporter(
                "Telemetry:Otlp:Endpoint",
                DotNetOtlpProtocol.Grpc,
                2048,
                512,
                5000,
                10000,
                DotNetTelemetryFailureDisposition.DropAndReport),
            new DotNetHttpDiagnosticProfile(
                kind == DotNetHostKind.Api,
                kind == DotNetHostKind.Api,
                kind == DotNetHostKind.Api,
                kind == DotNetHostKind.Api,
                kind == DotNetHostKind.Api,
                [],
                [],
                false,
                false),
            [],
            "Logging:LogLevel",
            false,
            5000);

    private static DotNetPackageReference Package(
        string id,
        string version,
        char digest) =>
        new(id, new SemanticVersion(version), Digest(digest));

    private static IntegratorDocumentProvenance Provenance(
        DotNetHostDefinition host,
        ArtifactReference operation) =>
        new(
            Ref("shell", "reviewed", '6'),
            host.GeneratorProfileRevision,
            [operation]);

    private static ArtifactCompatibility Compatibility() =>
        new(
            Id("policy", "compatibility"),
            [
                new CompatibilityClaim(
                    CompatibilityDimension.WireRead,
                    CompatibilityClassification.Unknown,
                    []),
            ],
            new SemanticVersionRange("[1.0.0]"),
            new SemanticVersionRange("[1.0.0]"),
            []);
}
