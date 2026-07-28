using System.Text;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Generation.FastEndpoints;
using Orbyss.ProgramKit.DotNet.Health;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Deterministic .NET 10 source renderer bound to the accepted CShells ABI.</summary>
public sealed class DotNetHostSourceRenderer : IDotNetHostSourceRenderer
{
    private readonly IDotNetConfigurationProjectionCompiler configurationCompiler;
    private readonly IDotNetTelemetryProjectionCompiler telemetryCompiler;
    private readonly IDotNetTransportFailureProjectionCompiler transportFailureCompiler;
    private readonly IDotNetSecurityProjectionCompiler securityCompiler;
    private readonly IDotNetFastEndpointsProjectionCompiler fastEndpointsCompiler;

    /// <summary>Initializes the renderer with the reusable configuration compiler.</summary>
    public DotNetHostSourceRenderer(
        IDotNetConfigurationProjectionCompiler configurationCompiler,
        IDotNetTelemetryProjectionCompiler telemetryCompiler,
        IDotNetTransportFailureProjectionCompiler transportFailureCompiler,
        IDotNetSecurityProjectionCompiler securityCompiler,
        IDotNetFastEndpointsProjectionCompiler fastEndpointsCompiler)
    {
        this.configurationCompiler = configurationCompiler ??
            throw new ArgumentNullException(nameof(configurationCompiler));
        this.telemetryCompiler = telemetryCompiler ??
            throw new ArgumentNullException(nameof(telemetryCompiler));
        this.transportFailureCompiler = transportFailureCompiler ??
            throw new ArgumentNullException(nameof(transportFailureCompiler));
        this.securityCompiler = securityCompiler ??
            throw new ArgumentNullException(nameof(securityCompiler));
        this.fastEndpointsCompiler = fastEndpointsCompiler ??
            throw new ArgumentNullException(nameof(fastEndpointsCompiler));
    }

    /// <inheritdoc />
    public ImmutableArray<GeneratedOutput> Render(
        DotNetHostDefinition host,
        DotNetHostLock hostLock,
        ImmutableArray<DotNetFeatureSelection> features,
        OpenApiDocumentProjection? openApiDocument)
    {
        ArgumentNullException.ThrowIfNull(host);
        ArgumentNullException.ThrowIfNull(hostLock);
        if (host.Kind == DotNetHostKind.Console)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.ConsoleProjectionFailed,
                "Console hosts require the typed Spectre Console generator.",
                "/host");
        }

        var outputs = ImmutableArray.CreateBuilder<GeneratedOutput>();
        outputs.Add(new GeneratedOutput("global.json", DotNetSourceText.Utf8(RenderGlobalJson())));
        outputs.Add(new GeneratedOutput("Directory.Build.props", DotNetSourceText.Utf8(RenderBuildPolicy())));
        outputs.Add(new GeneratedOutput("Directory.Build.targets", DotNetSourceText.Utf8(RenderBuildTargets())));
        outputs.Add(new GeneratedOutput("Directory.Packages.props", DotNetSourceText.Utf8(RenderPackagePolicy())));
        outputs.Add(new GeneratedOutput("GeneratedHost.csproj", DotNetSourceText.Utf8(RenderProject(host, hostLock))));
        outputs.Add(new GeneratedOutput(
            "ProgramKitGenerated/Composition/Program.cs",
            DotNetSourceText.Utf8(RenderProgram(
                host,
                features,
                configurationCompiler.RenderRegistration(host),
                telemetryCompiler.RenderRegistration(host),
                telemetryCompiler.RenderMiddleware(host),
                transportFailureCompiler.RenderRegistration(host),
                transportFailureCompiler.RenderMiddleware(host),
                securityCompiler.RenderRegistration(host),
                securityCompiler.RenderMiddleware(host)))));
        outputs.AddRange(configurationCompiler.Compile(host));
        outputs.AddRange(telemetryCompiler.Compile(host));
        outputs.AddRange(transportFailureCompiler.Compile(host));
        outputs.AddRange(securityCompiler.Compile(host));
        outputs.AddRange(fastEndpointsCompiler.Compile(host, openApiDocument));
        return outputs.ToImmutable();
    }

    private static string RenderGlobalJson() =>
        """
        {
          "sdk": {
            "version": "10.0.302",
            "rollForward": "disable",
            "allowPrerelease": false
          }
        }
        """;

    private static string RenderBuildPolicy() =>
        """
        <Project>
          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <LangVersion>14.0</LangVersion>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <CodeAnalysisTreatWarningsAsErrors>true</CodeAnalysisTreatWarningsAsErrors>
            <MSBuildTreatWarningsAsErrors>true</MSBuildTreatWarningsAsErrors>
            <RestoreTreatWarningsAsErrors>true</RestoreTreatWarningsAsErrors>
            <NoWarn>__ProgramKitNoWarningSuppression__</NoWarn>
            <WarningsNotAsErrors>__ProgramKitNoWarningDemotion__</WarningsNotAsErrors>
            <TargetFrameworks></TargetFrameworks>
          </PropertyGroup>
        </Project>
        """;

    private static string RenderBuildTargets() =>
        """
        <Project />
        """;

    private static string RenderPackagePolicy() =>
        """
        <Project />
        """;

    private static string RenderProject(
        DotNetHostDefinition host,
        DotNetHostLock hostLock)
    {
        var sdk = host.Kind == DotNetHostKind.Api || host.Health is not null
            ? "Microsoft.NET.Sdk.Web"
            : "Microsoft.NET.Sdk";
        var builder = new StringBuilder();
        builder.Append("<Project Sdk=\"").Append(sdk).AppendLine("\">");
        builder.AppendLine("  <PropertyGroup>");
        builder.AppendLine("    <OutputType>Exe</OutputType>");
        builder.AppendLine("    <RootNamespace>GeneratedHost</RootNamespace>");
        builder.AppendLine("    <AssemblyName>GeneratedHost</AssemblyName>");
        builder.AppendLine("    <EnableConfigurationBindingGenerator>true</EnableConfigurationBindingGenerator>");
        builder.AppendLine("  </PropertyGroup>");
        builder.AppendLine("  <ItemGroup>");
        foreach (var package in hostLock.Packages.OrderBy(static item => item.PackageId, StringComparer.Ordinal))
        {
            builder
                .Append("    <PackageReference Include=\"")
                .Append(DotNetSourceText.Xml(package.PackageId))
                .Append("\" Version=\"[")
                .Append(DotNetSourceText.Xml(package.Version.Value))
                .AppendLine("]\" />");
        }

        builder.AppendLine("  </ItemGroup>");
        builder.AppendLine("</Project>");
        return builder.ToString();
    }

    private static string RenderProgram(
        DotNetHostDefinition host,
        ImmutableArray<DotNetFeatureSelection> features,
        string configurationRegistration,
        string telemetryRegistration,
        string telemetryMiddleware,
        string transportFailureRegistration,
        string transportFailureMiddleware,
        string securityRegistration,
        string securityMiddleware)
    {
        var web = host.Kind == DotNetHostKind.Api || host.Health is not null;
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("using CShells.Configuration;");
        builder.AppendLine("using Microsoft.Extensions.Configuration;");
        builder.AppendLine("using Microsoft.Extensions.DependencyInjection;");
        if (host.Telemetry is not null)
        {
            builder.AppendLine("using Microsoft.Extensions.Logging;");
            builder.AppendLine("using OpenTelemetry.Logs;");
            builder.AppendLine("using OpenTelemetry.Metrics;");
            builder.AppendLine("using OpenTelemetry.Resources;");
            builder.AppendLine("using OpenTelemetry.Trace;");
        }
        if (web)
        {
            builder.AppendLine("using CShells.AspNetCore.Extensions;");
            builder.AppendLine("using Microsoft.AspNetCore.Diagnostics.HealthChecks;");
            builder.AppendLine("using Microsoft.Extensions.Diagnostics.HealthChecks;");
            if (host.Telemetry?.HttpDiagnostics.Enabled == true)
            {
                builder.AppendLine("using Microsoft.AspNetCore.HttpLogging;");
            }
            if (host.Security is not null)
            {
                builder.AppendLine("using Microsoft.AspNetCore.Authentication.Cookies;");
                builder.AppendLine("using Microsoft.AspNetCore.Authentication.JwtBearer;");
                builder.AppendLine("using Microsoft.AspNetCore.Authentication.OpenIdConnect;");
                builder.AppendLine("using Microsoft.AspNetCore.Authorization;");
            }
        }
        else
        {
            builder.AppendLine("using CShells.DependencyInjection;");
            builder.AppendLine("using Microsoft.Extensions.Hosting;");
        }

        if (!host.TaskRuntimeRequirements.IsDefaultOrEmpty)
        {
            builder.AppendLine("using Orbyss.ProgramKit.Artifacts.Primitives;");
            builder.AppendLine("using Orbyss.ProgramKit.Artifacts.References;");
            builder.AppendLine("using Orbyss.ProgramKit.Tasks.Hosting.Composition;");
            builder.AppendLine("using Orbyss.ProgramKit.Tasks.InProcess.Composition;");
        }

        builder.AppendLine();
        builder.AppendLine("namespace GeneratedHost.Composition;");
        builder.AppendLine();
        builder.AppendLine("internal static partial class Program");
        builder.AppendLine("{");
        builder.AppendLine("    private static async Task<int> Main(string[] args)");
        builder.AppendLine("    {");
        builder.AppendLine(web
            ? "var builder = WebApplication.CreateBuilder(args);"
            : "var builder = Host.CreateApplicationBuilder(args);");
        builder.Append(configurationRegistration);
        builder.Append(telemetryRegistration);
        builder.Append(transportFailureRegistration);
        builder.Append(securityRegistration);
        if (host.Telemetry?.HttpDiagnostics.Enabled == true)
        {
            RenderHttpLoggingRegistration(builder);
        }

        if (web)
        {
            RenderWebComposition(builder, host, features);
        }
        else
        {
            RenderGenericComposition(builder, host, features);
        }

        RenderTaskRuntime(builder, host);
        builder.AppendLine(web
            ? "var app = builder.Build();"
            : "using var host = builder.Build();");
        if (web)
        {
            builder.Append(transportFailureMiddleware);
            builder.Append(telemetryMiddleware);
            builder.Append(securityMiddleware);
            RenderHealthMappings(builder, host.Health);
            builder.AppendLine("app.MapShells();");
            builder.AppendLine("await app.RunAsync();");
        }
        else
        {
            builder.AppendLine("await host.RunAsync();");
        }

        builder.AppendLine("return 0;");
        builder.AppendLine("    }");
        builder.AppendLine("}");

        return builder.ToString();
    }

    private static void RenderHttpLoggingRegistration(StringBuilder builder)
    {
        builder.AppendLine("builder.Logging.AddFilter(");
        builder.AppendLine("    \"Microsoft.AspNetCore.Hosting.Diagnostics\",");
        builder.AppendLine("    LogLevel.Warning);");
        builder.AppendLine("builder.Services.AddHttpLogging(options =>");
        builder.AppendLine("{");
        builder.AppendLine("    options.CombineLogs = true;");
        builder.AppendLine("    options.LoggingFields =");
        builder.AppendLine("        HttpLoggingFields.RequestMethod |");
        builder.AppendLine("        HttpLoggingFields.RequestPath |");
        builder.AppendLine("        HttpLoggingFields.ResponseStatusCode |");
        builder.AppendLine("        HttpLoggingFields.Duration;");
        builder.AppendLine("    options.RequestHeaders.Clear();");
        builder.AppendLine("    options.ResponseHeaders.Clear();");
        builder.AppendLine("    options.RequestBodyLogLimit = 0;");
        builder.AppendLine("    options.ResponseBodyLogLimit = 0;");
        builder.AppendLine("});");
    }

    private static void RenderWebComposition(
        StringBuilder builder,
        DotNetHostDefinition host,
        ImmutableArray<DotNetFeatureSelection> features)
    {
        if (host.Health is not null)
        {
            builder.AppendLine("builder.Services.AddHealthChecks();");
            builder.AppendLine("builder.WebHost.ConfigureKestrel(options =>");
            builder.AppendLine("{");
            foreach (var listener in host.Health.Listeners.OrderBy(static item => item.Identity.Value, StringComparer.Ordinal))
            {
                builder
                    .Append("    options.Listen(System.Net.IPAddress.Parse(")
                    .Append(DotNetSourceText.CSharpLiteral(NormalizeAddress(listener.Address)))
                    .Append("), ")
                    .Append(listener.Port);
                if (string.Equals(listener.Scheme, "https", StringComparison.Ordinal))
                {
                    builder.AppendLine(", listen => listen.UseHttps());");
                }
                else
                {
                    builder.AppendLine(");");
                }
            }

            builder.AppendLine("});");
        }

        builder.AppendLine("builder.AddShells(cshells =>");
        builder.AppendLine("{");
        RenderShell(builder, host, features, "    ");
        builder.AppendLine("});");
    }

    private static void RenderGenericComposition(
        StringBuilder builder,
        DotNetHostDefinition host,
        ImmutableArray<DotNetFeatureSelection> features)
    {
        builder.AppendLine("builder.Services.AddCShells(cshells =>");
        builder.AppendLine("{");
        RenderShell(builder, host, features, "    ");
        builder.AppendLine("});");
    }

    private static void RenderShell(
        StringBuilder builder,
        DotNetHostDefinition host,
        ImmutableArray<DotNetFeatureSelection> features,
        string indent)
    {
        foreach (var shellIdentity in host.ShellIdentities.OrderBy(static item => item.Value, StringComparer.Ordinal))
        {
            builder
                .Append(indent)
                .Append("cshells.AddShell(")
                .Append(DotNetSourceText.CSharpLiteral(shellIdentity.Value))
                .AppendLine(", shell =>");
            builder.Append(indent).AppendLine("{");
            foreach (var feature in features.Where(feature => feature.ShellIdentity == shellIdentity))
            {
                builder
                    .Append(indent)
                    .Append("    shell.WithFeature(typeof(global::")
                    .Append(feature.FeatureTypeName)
                    .AppendLine("));");
            }

            if (host.FastEndpoints is not null)
            {
                builder
                    .Append(indent)
                    .AppendLine(
                        "    shell.WithFeature(typeof(global::GeneratedHost.Hosting.ProgramKitFastEndpointsFeature));");
            }

            builder.Append(indent).AppendLine("});");
        }
    }

    private static void RenderTaskRuntime(
        StringBuilder builder,
        DotNetHostDefinition host)
    {
        if (host.TaskRuntimeRequirements.IsDefaultOrEmpty)
        {
            return;
        }

        var revision = host.TaskRuntimeRequirements[0].RuntimeRevision;
        builder.AppendLine("var taskRuntimeRevision = new ArtifactReference(");
        builder
            .Append("    new ProgramKitIdentifier(")
            .Append(DotNetSourceText.CSharpLiteral(revision.Identity.Value))
            .AppendLine("),");
        builder
            .Append("    new SemanticVersion(")
            .Append(DotNetSourceText.CSharpLiteral(revision.Version.Value))
            .AppendLine("),");
        builder
            .Append("    new Sha256Digest(")
            .Append(DotNetSourceText.CSharpLiteral(revision.Digest.Value))
            .AppendLine("));");
        builder.AppendLine("var taskRuntimeOptions = new InProcessTaskRuntimeOptions");
        builder.AppendLine("{");
        builder.AppendLine("    RuntimeRevision = taskRuntimeRevision,");
        builder.AppendLine("};");
        builder.AppendLine("builder.Services.UseInProcessTaskRuntime(taskRuntimeOptions);");
        builder.AppendLine("var taskHostingOptions = new TaskHostingOptions();");
        builder.AppendLine("builder.Services.AddProgramKitTaskHosting(taskHostingOptions);");
    }

    private static void RenderHealthMappings(
        StringBuilder builder,
        DotNetHealthConfiguration? health)
    {
        if (health is null)
        {
            return;
        }

        builder.AppendLine("app.Use(async (context, next) =>");
        builder.AppendLine("{");
        foreach (var endpoint in health.Endpoints.OrderBy(static item => item.Path, StringComparer.Ordinal))
        {
            var listener = health.Listeners.Single(item => item.Identity == endpoint.ListenerIdentity);
            builder
                .Append("    if (context.Request.Path == ")
                .Append(DotNetSourceText.CSharpLiteral(endpoint.Path))
                .Append(" && context.Connection.LocalPort != ")
                .Append(listener.Port)
                .AppendLine(")");
            builder.AppendLine("    {");
            builder.AppendLine("        context.Response.StatusCode = StatusCodes.Status404NotFound;");
            builder.AppendLine("        return;");
            builder.AppendLine("    }");
        }

        builder.AppendLine();
        builder.AppendLine("    await next(context);");
        builder.AppendLine("});");
        foreach (var endpoint in health.Endpoints.OrderBy(static item => item.Path, StringComparer.Ordinal))
        {
            var listener = health.Listeners.Single(item => item.Identity == endpoint.ListenerIdentity);
            builder
                .Append("var healthOptions")
                .Append(HealthVariable(endpoint.Path))
                .AppendLine(" = new HealthCheckOptions");
            builder.AppendLine("{");
            builder.AppendLine("    AllowCachingResponses = false,");
            builder.AppendLine("    ResultStatusCodes =");
            builder.AppendLine("    {");
            builder.Append("        [HealthStatus.Healthy] = ").Append(endpoint.StatusCodes.Healthy).AppendLine(",");
            builder.Append("        [HealthStatus.Degraded] = ").Append(endpoint.StatusCodes.Degraded).AppendLine(",");
            builder.Append("        [HealthStatus.Unhealthy] = ").Append(endpoint.StatusCodes.Unhealthy).AppendLine(",");
            builder.AppendLine("    },");
            if (!endpoint.IncludeTags.IsDefaultOrEmpty || !endpoint.ExcludeTags.IsDefaultOrEmpty)
            {
                builder.AppendLine("    Predicate = registration =>");
                builder.Append("        ");
                RenderTagPredicate(builder, endpoint);
                builder.AppendLine(",");
            }

            builder.AppendLine("};");
            builder
                .Append("var healthEndpoint")
                .Append(HealthVariable(endpoint.Path))
                .Append(" = app.MapHealthChecks(")
                .Append(DotNetSourceText.CSharpLiteral(endpoint.Path))
                .Append(", healthOptions")
                .Append(HealthVariable(endpoint.Path))
                .AppendLine(");");
            if (listener.Exposure != DotNetHealthExposure.Loopback)
            {
                builder
                    .Append("healthEndpoint")
                    .Append(HealthVariable(endpoint.Path))
                    .Append(".RequireAuthorization(")
                    .Append(DotNetSourceText.CSharpLiteral(
                        endpoint.AuthorizationRevision.Identity.Value))
                    .AppendLine(");");
                builder
                    .Append("healthEndpoint")
                    .Append(HealthVariable(endpoint.Path))
                    .Append(".RequireHost(")
                    .Append(DotNetSourceText.CSharpLiteral(listener.Address))
                    .AppendLine(");");
            }
        }
    }

    private static void RenderTagPredicate(
        StringBuilder builder,
        DotNetHealthEndpoint endpoint)
    {
        var predicates = new List<string>();
        foreach (var tag in endpoint.IncludeTags.Order(StringComparer.Ordinal))
        {
            predicates.Add(string.Concat(
                "registration.Tags.Contains(",
                DotNetSourceText.CSharpLiteral(tag),
                ", StringComparer.Ordinal)"));
        }

        foreach (var tag in endpoint.ExcludeTags.Order(StringComparer.Ordinal))
        {
            predicates.Add(string.Concat(
                "!registration.Tags.Contains(",
                DotNetSourceText.CSharpLiteral(tag),
                ", StringComparer.Ordinal)"));
        }

        builder.Append(predicates.Count == 0
            ? "true"
            : string.Join(" && ", predicates));
    }

    private static string NormalizeAddress(string value) =>
        value switch
        {
            "localhost" => "127.0.0.1",
            _ => value,
        };

    private static string HealthVariable(string path)
    {
        var characters = path
            .Where(char.IsLetterOrDigit)
            .ToArray();
        return characters.Length == 0 ? "Root" : new string(characters);
    }
}
