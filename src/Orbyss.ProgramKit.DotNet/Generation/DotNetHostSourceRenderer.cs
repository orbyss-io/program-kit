using System.Text;
using System.Globalization;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Generation.ConsoleCommands;
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
        OpenApiDocumentProjection? openApiDocument,
        OpenConsoleDocument? consoleDocument)
    {
        ArgumentNullException.ThrowIfNull(host);
        ArgumentNullException.ThrowIfNull(hostLock);
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
        if (host.Kind == DotNetHostKind.Console && consoleDocument is not null)
        {
            outputs.Add(new GeneratedOutput(
                DotNetConsoleCommandDispatchContract.DispatcherContractPath,
                DotNetSourceText.Utf8(
                    DotNetConsoleCommandDispatchContract.DispatcherSource)));
            outputs.Add(new GeneratedOutput(
                "ProgramKitGenerated/Commands/GeneratedConsoleParseResult.cs",
                DotNetSourceText.Utf8(RenderParseResult())));
            outputs.Add(new GeneratedOutput(
                "ProgramKitGenerated/Commands/GeneratedConsoleParser.cs",
                DotNetSourceText.Utf8(RenderParser(consoleDocument))));
        }

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
        if (host.Kind == DotNetHostKind.Console)
        {
            builder.AppendLine("var parseResult = GeneratedHost.Commands.GeneratedConsoleParser.Parse(args);");
            builder.AppendLine("if (!parseResult.Success)");
            builder.AppendLine("{");
            builder.AppendLine("    global::System.Console.Error.WriteLine(parseResult.Diagnostic);");
            builder.AppendLine("    return parseResult.ExitCode;");
            builder.AppendLine("}");
            builder.AppendLine("if (!parseResult.InvokeCommand)");
            builder.AppendLine("{");
            builder.AppendLine("    global::System.Console.Out.WriteLine(parseResult.Output);");
            builder.AppendLine("    return parseResult.ExitCode;");
            builder.AppendLine("}");
            builder.AppendLine();
        }

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
        if (host.Kind == DotNetHostKind.Console)
        {
            builder.AppendLine("ConfigureProgramKitConsoleServices(builder.Services);");
            RenderConsoleInvocation(
                builder,
                web,
                host,
                transportFailureMiddleware,
                telemetryMiddleware,
                securityMiddleware);
        }
        else
        {
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
        }

        builder.AppendLine("    }");
        if (host.Kind == DotNetHostKind.Console)
        {
            builder.AppendLine();
            builder.AppendLine("    static partial void ConfigureProgramKitConsoleServices(");
            builder.AppendLine("        IServiceCollection services);");
        }

        builder.AppendLine("}");

        return builder.ToString();
    }

    private static void RenderConsoleInvocation(
        StringBuilder builder,
        bool web,
        DotNetHostDefinition host,
        string transportFailureMiddleware,
        string telemetryMiddleware,
        string securityMiddleware)
    {
        var application = web ? "app" : "host";
        builder.AppendLine(web
            ? "await using var app = builder.Build();"
            : "using var host = builder.Build();");
        if (web)
        {
            builder.Append(transportFailureMiddleware);
            builder.Append(telemetryMiddleware);
            builder.Append(securityMiddleware);
            RenderHealthMappings(builder, host.Health);
            builder.AppendLine("app.MapShells();");
        }

        builder
            .Append("var dispatchers = ")
            .Append(application)
            .AppendLine(".Services");
        builder.AppendLine("    .GetServices<GeneratedHost.Commands.IProgramKitConsoleCommandDispatcher>()");
        builder.AppendLine("    .ToArray();");
        builder.AppendLine("if (dispatchers.Length != 1)");
        builder.AppendLine("{");
        builder.AppendLine("    throw new InvalidOperationException(");
        builder.AppendLine("        \"Exactly one IProgramKitConsoleCommandDispatcher registration is required.\");");
        builder.AppendLine("}");
        builder.AppendLine("var dispatcher = dispatchers[0];");
        builder
            .Append("var applicationLifetime = ")
            .Append(application)
            .AppendLine(".Services.GetRequiredService<");
        builder.AppendLine("    global::Microsoft.Extensions.Hosting.IHostApplicationLifetime>();");
        builder.AppendLine("try");
        builder.AppendLine("{");
        builder
            .Append("    await ")
            .Append(application)
            .AppendLine(".StartAsync();");
        builder.AppendLine("    return await dispatcher.DispatchAsync(");
        builder.AppendLine("        parseResult,");
        builder.AppendLine("        applicationLifetime.ApplicationStopping);");
        builder.AppendLine("}");
        builder.AppendLine("finally");
        builder.AppendLine("{");
        builder.AppendLine("    using var stopCancellation = new CancellationTokenSource(");
        builder.AppendLine("        TimeSpan.FromSeconds(30));");
        builder
            .Append("    await ")
            .Append(application)
            .AppendLine(".StopAsync(stopCancellation.Token);");
        builder.AppendLine("}");
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

    private static string RenderParseResult() =>
        """
        // <auto-generated program-kit>
        namespace GeneratedHost.Commands;

        internal sealed record GeneratedConsoleParseResult(
            bool Success,
            bool InvokeCommand,
            int ExitCode,
            string Diagnostic,
            string Output,
            string Command,
            IReadOnlyDictionary<string, IReadOnlyList<string>> Options,
            IReadOnlyList<string> Arguments);
        """;

    private static string RenderParser(OpenConsoleDocument document)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("using System.Globalization;");
        builder.AppendLine();
        builder.AppendLine("namespace GeneratedHost.Commands;");
        builder.AppendLine();
        builder.AppendLine("internal static class GeneratedConsoleParser");
        builder.AppendLine("{");
        RenderCommandPaths(builder, document);
        RenderOptionAliases(builder, document);
        builder.AppendLine("    internal static GeneratedConsoleParseResult Parse(string[] args)");
        builder.AppendLine("    {");
        builder.AppendLine("        ArgumentNullException.ThrowIfNull(args);");
        builder.AppendLine("        if (TryRenderInformation(args, out var information))");
        builder.AppendLine("        {");
        builder.AppendLine("            return information;");
        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        var command = ResolveCommand(args, out var commandTokens);");
        builder.AppendLine("        if (command.Length == 0)");
        builder.AppendLine("        {");
        builder.AppendLine("            return Failure(\"PKNETC001 A known command path is required.\", 2);");
        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        var options = new Dictionary<string, List<string>>(StringComparer.Ordinal);");
        builder.AppendLine("        var occurrences = new Dictionary<string, int>(StringComparer.Ordinal);");
        builder.AppendLine("        var arguments = new List<string>();");
        builder.AppendLine("        var terminated = false;");
        builder.AppendLine("        for (var index = commandTokens; index < args.Length; index++)");
        builder.AppendLine("        {");
        builder.AppendLine("            var token = args[index];");
        builder.AppendLine("            if (!terminated && token == \"--\")");
        builder.AppendLine("            {");
        builder.AppendLine("                terminated = true;");
        builder.AppendLine("                continue;");
        builder.AppendLine("            }");
        builder.AppendLine();
        builder.AppendLine("            if (!terminated && token.StartsWith('-'))");
        builder.AppendLine("            {");
        builder.AppendLine("                var separator = token.IndexOf('=');");
        builder.AppendLine("                var name = separator < 0 ? token : token[..separator];");
        builder.AppendLine("                var canonical = NormalizeOption(name);");
        builder.AppendLine("                if (canonical.Length == 0 || !IsAllowed(command, canonical))");
        builder.AppendLine("                {");
        builder.AppendLine("                    return Failure(string.Concat(\"PKNETC002 Unknown option: \", name), 2);");
        builder.AppendLine("                }");
        builder.AppendLine();
        builder.AppendLine("                occurrences.TryGetValue(canonical, out var occurrence);");
        builder.AppendLine("                if (occurrence >= MaximumOccurrences(command, canonical))");
        builder.AppendLine("                {");
        builder.AppendLine("                    return Failure(string.Concat(\"PKNETC003 Option occurrence exceeded: \", canonical), 2);");
        builder.AppendLine("                }");
        builder.AppendLine();
        builder.AppendLine("                occurrences[canonical] = occurrence + 1;");
        builder.AppendLine("                if (!options.TryGetValue(canonical, out var values))");
        builder.AppendLine("                {");
        builder.AppendLine("                    values = [];");
        builder.AppendLine("                    options.Add(canonical, values);");
        builder.AppendLine("                }");
        builder.AppendLine();
        builder.AppendLine("                if (RequiresValue(command, canonical))");
        builder.AppendLine("                {");
        builder.AppendLine("                    var occurrenceValues = new List<string>();");
        builder.AppendLine("                    if (separator >= 0)");
        builder.AppendLine("                    {");
        builder.AppendLine("                        occurrenceValues.Add(token[(separator + 1)..]);");
        builder.AppendLine("                    }");
        builder.AppendLine("                    else");
        builder.AppendLine("                    {");
        builder.AppendLine("                        var maximumValues = MaximumValues(command, canonical);");
        builder.AppendLine("                        while (occurrenceValues.Count < maximumValues && index + 1 < args.Length)");
        builder.AppendLine("                        {");
        builder.AppendLine("                            var candidate = args[index + 1];");
        builder.AppendLine("                            var candidateSeparator = candidate.IndexOf('=');");
        builder.AppendLine("                            var candidateName = candidateSeparator < 0 ? candidate : candidate[..candidateSeparator];");
        builder.AppendLine("                            if (candidate == \"--\" || NormalizeOption(candidateName).Length != 0)");
        builder.AppendLine("                            {");
        builder.AppendLine("                                break;");
        builder.AppendLine("                            }");
        builder.AppendLine();
        builder.AppendLine("                            occurrenceValues.Add(candidate);");
        builder.AppendLine("                            index++;");
        builder.AppendLine("                        }");
        builder.AppendLine("                    }");
        builder.AppendLine();
        builder.AppendLine("                    if (occurrenceValues.Count < MinimumValues(command, canonical) ||");
        builder.AppendLine("                        occurrenceValues.Count > MaximumValues(command, canonical) ||");
        builder.AppendLine("                        occurrenceValues.Any(value => string.IsNullOrEmpty(value) || !HasValidType(command, canonical, value)))");
        builder.AppendLine("                    {");
        builder.AppendLine("                        return Failure(string.Concat(\"PKNETC004 Invalid option value: \", canonical), 2);");
        builder.AppendLine("                    }");
        builder.AppendLine();
        builder.AppendLine("                    values.AddRange(occurrenceValues);");
        builder.AppendLine("                }");
        builder.AppendLine("                else");
        builder.AppendLine("                {");
        builder.AppendLine("                    values.Add(\"true\");");
        builder.AppendLine("                }");
        builder.AppendLine();
        builder.AppendLine("                continue;");
        builder.AppendLine("            }");
        builder.AppendLine();
        builder.AppendLine("            arguments.Add(token);");
        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        ApplyDefaults(command, options, occurrences);");
        builder.AppendLine("        var contractDiagnostic = ValidateContract(command, options, arguments);");
        builder.AppendLine("        if (contractDiagnostic.Length != 0)");
        builder.AppendLine("        {");
        builder.AppendLine("            return Failure(contractDiagnostic, 2);");
        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        var readOnly = options.ToDictionary(");
        builder.AppendLine("            static pair => pair.Key,");
        builder.AppendLine("            static pair => (IReadOnlyList<string>)pair.Value,");
        builder.AppendLine("            StringComparer.Ordinal);");
        builder.AppendLine("        return new GeneratedConsoleParseResult(true, true, 0, string.Empty, string.Empty, command, readOnly, arguments);");
        builder.AppendLine("    }");
        RenderParserMethods(builder, document);
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static void RenderCommandPaths(
        StringBuilder builder,
        OpenConsoleDocument document)
    {
        var paths = document.Commands
            .SelectMany(command =>
                command.Aliases
                    .Prepend(command.Path)
                    .Select(path => new
                    {
                        Path = path,
                        Command = string.Join(" ", command.Path),
                    }))
            .OrderByDescending(static item => item.Path.Length)
            .ThenBy(static item => string.Join(" ", item.Path), StringComparer.Ordinal);
        builder.AppendLine("    private static readonly (string[] Path, string Command)[] CommandPaths =");
        builder.AppendLine("    [");
        foreach (var path in paths)
        {
            builder
                .Append("        ([")
                .Append(string.Join(", ", path.Path.Select(DotNetSourceText.CSharpLiteral)))
                .Append("], ")
                .Append(DotNetSourceText.CSharpLiteral(path.Command))
                .AppendLine("),");
        }

        builder.AppendLine("    ];");
        builder.AppendLine();
    }

    private static void RenderOptionAliases(
        StringBuilder builder,
        OpenConsoleDocument document)
    {
        var options = document.GlobalOptions
            .Concat(document.Commands.SelectMany(static command => command.Options))
            .DistinctBy(static option => option.LongName)
            .OrderBy(static option => option.LongName, StringComparer.Ordinal);
        builder.AppendLine("    private static string NormalizeOption(string value) =>");
        builder.AppendLine("        value switch");
        builder.AppendLine("        {");
        foreach (var option in options)
        {
            var names = option.Aliases
                .Append(string.Concat("--", option.LongName))
                .Concat(option.ShortName is null ? [] : [string.Concat("-", option.ShortName)])
                .Distinct(StringComparer.Ordinal);
            foreach (var name in names)
            {
                builder
                    .Append("            ")
                    .Append(DotNetSourceText.CSharpLiteral(name))
                    .Append(" => ")
                    .Append(DotNetSourceText.CSharpLiteral(option.LongName))
                    .AppendLine(",");
            }
        }

        builder.AppendLine("            _ => string.Empty,");
        builder.AppendLine("        };");
        builder.AppendLine();
    }

    private static void RenderParserMethods(
        StringBuilder builder,
        OpenConsoleDocument document)
    {
        RenderInformationMethods(builder, document);
        builder.AppendLine();
        builder.AppendLine("    private static string ResolveCommand(string[] args, out int consumed)");
        builder.AppendLine("    {");
        builder.AppendLine("        foreach (var candidate in CommandPaths)");
        builder.AppendLine("        {");
        builder.AppendLine("            if (args.Length >= candidate.Path.Length &&");
        builder.AppendLine("                candidate.Path.Where((part, index) => args[index] == part).Count() == candidate.Path.Length)");
        builder.AppendLine("            {");
        builder.AppendLine("                consumed = candidate.Path.Length;");
        builder.AppendLine("                return candidate.Command;");
        builder.AppendLine("            }");
        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        consumed = 0;");
        builder.AppendLine("        return string.Empty;");
        builder.AppendLine("    }");
        RenderCommandOptionSwitch(builder, document, "IsAllowed", static option => "true", "false");
        RenderCommandOptionSwitch(builder, document, "RequiresValue", static option => option.Kind == ConsoleOptionKind.Value ? "true" : "false", "false");
        RenderCommandOptionSwitch(builder, document, "MinimumValues", static option => option.ValueArity.Minimum.ToString(CultureInfo.InvariantCulture), "0", "int");
        RenderCommandOptionSwitch(builder, document, "MaximumValues", static option => option.ValueArity.Maximum.ToString(CultureInfo.InvariantCulture), "0", "int");
        RenderCommandOptionSwitch(builder, document, "MaximumOccurrences", static option => option.Occurrence.Maximum.ToString(CultureInfo.InvariantCulture), "0", "int");
        builder.AppendLine();
        builder.AppendLine("    private static bool HasValidType(string command, string option, string value)");
        builder.AppendLine("        => HasValidValueType(ValueType(command, option), value);");
        builder.AppendLine();
        builder.AppendLine("    private static bool HasValidValueType(string type, string value)");
        builder.AppendLine("    {");
        builder.AppendLine("        return type switch");
        builder.AppendLine("        {");
        builder.AppendLine("            \"string\" => true,");
        builder.AppendLine("            \"boolean\" => bool.TryParse(value, out _),");
        builder.AppendLine("            \"int32\" => int.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out _),");
        builder.AppendLine("            \"int64\" => long.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out _),");
        builder.AppendLine("            \"decimal\" => decimal.TryParse(value, NumberStyles.Number, CultureInfo.InvariantCulture, out _),");
        builder.AppendLine("            \"guid\" => Guid.TryParseExact(value, \"D\", out _),");
        builder.AppendLine("            \"date-time\" => DateTimeOffset.TryParseExact(value, \"O\", CultureInfo.InvariantCulture, DateTimeStyles.None, out _),");
        builder.AppendLine("            _ => false,");
        builder.AppendLine("        };");
        builder.AppendLine("    }");
        RenderCommandOptionSwitch(builder, document, "ValueType", static option => DotNetSourceText.CSharpLiteral(option.ValueType), "string.Empty", "string");
        RenderDefaultApplication(builder, document);
        RenderContractValidation(builder, document);
        builder.AppendLine();
        builder.AppendLine("    private static GeneratedConsoleParseResult Failure(string diagnostic, int exitCode) =>");
        builder.AppendLine("        new(false, false, exitCode, diagnostic, string.Empty, string.Empty, new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal), []);");
    }

    private static void RenderInformationMethods(
        StringBuilder builder,
        OpenConsoleDocument document)
    {
        var commandCandidates = document.Commands
            .SelectMany(command => document.Completion.IncludesAliases
                ? command.Aliases.Prepend(command.Path)
                : [command.Path])
            .Select(static path => string.Join(" ", path))
            .ToArray();
        var options = document.GlobalOptions
            .Concat(document.Commands.SelectMany(static command => command.Options))
            .ToArray();
        var optionCandidates = options
            .SelectMany(option => document.Completion.IncludesAliases
                ? option.Aliases
                    .Append(string.Concat("--", option.LongName))
                    .Concat(option.ShortName is null
                        ? []
                        : [string.Concat("-", option.ShortName)])
                : [string.Concat("--", option.LongName)]);
        var valueCandidates = document.Completion.IncludesValueHints
            ? options
                .Where(static option => option.Kind == ConsoleOptionKind.Value)
                .Select(static option => string.Concat(
                    "--",
                    option.LongName,
                    "=<",
                    option.ValueType,
                    ">"))
            : [];
        var completionCandidates = commandCandidates
            .Concat(optionCandidates)
            .Concat(valueCandidates)
            .Distinct(StringComparer.Ordinal)
            .Order(StringComparer.Ordinal)
            .ToArray();
        builder.AppendLine();
        builder.AppendLine("    private static readonly string[] CompletionCandidates =");
        builder.AppendLine("    [");
        foreach (var candidate in completionCandidates)
        {
            builder
                .Append("        ")
                .Append(DotNetSourceText.CSharpLiteral(candidate))
                .AppendLine(",");
        }

        builder.AppendLine("    ];");
        builder.AppendLine();
        builder.AppendLine("    private static bool TryRenderInformation(");
        builder.AppendLine("        string[] args,");
        builder.AppendLine("        out GeneratedConsoleParseResult result)");
        builder.AppendLine("    {");
        builder.AppendLine("        var completionIndex = Array.IndexOf(args, " +
                           DotNetSourceText.CSharpLiteral(
                               string.Concat("--", document.Completion.LongOption)) +
                           ");");
        builder.AppendLine("        if (completionIndex >= 0)");
        builder.AppendLine("        {");
        builder.AppendLine("            var prefix = completionIndex + 1 < args.Length ? args[completionIndex + 1] : string.Empty;");
        builder.AppendLine("            var output = string.Join(Environment.NewLine, CompletionCandidates.Where(candidate => candidate.StartsWith(prefix, StringComparison.Ordinal)));");
        builder.AppendLine("            result = Information(string.Empty, output, 0);");
        builder.AppendLine("            return true;");
        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        var helpIndex = Array.FindIndex(args, token =>");
        builder
            .Append("            token == ")
            .Append(DotNetSourceText.CSharpLiteral(
                string.Concat("--", document.Help.LongOption)))
            .Append(" || token == ")
            .Append(DotNetSourceText.CSharpLiteral(
                string.Concat("-", document.Help.ShortOption)))
            .AppendLine(");");
        builder.AppendLine("        if (helpIndex >= 0)");
        builder.AppendLine("        {");
        builder.AppendLine("            var command = ResolveCommand(args, out _);");
        builder.AppendLine("            result = Information(command, RenderHelp(command), " +
                           document.Help.ExitCode.ToString(CultureInfo.InvariantCulture) +
                           ");");
        builder.AppendLine("            return true;");
        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        result = default!;");
        builder.AppendLine("        return false;");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    private static string RenderHelp(string command) =>");
        builder.AppendLine("        command switch");
        builder.AppendLine("        {");
        foreach (var command in document.Commands
                     .OrderBy(static item => string.Join(" ", item.Path), StringComparer.Ordinal))
        {
            builder
                .Append("            ")
                .Append(DotNetSourceText.CSharpLiteral(string.Join(" ", command.Path)))
                .Append(" => ")
                .Append(DotNetSourceText.CSharpLiteral(BuildCommandHelp(document, command)))
                .AppendLine(",");
        }

        builder
            .Append("            _ => ")
            .Append(DotNetSourceText.CSharpLiteral(BuildRootHelp(document)))
            .AppendLine(",");
        builder.AppendLine("        };");
        builder.AppendLine();
        builder.AppendLine("    private static GeneratedConsoleParseResult Information(");
        builder.AppendLine("        string command,");
        builder.AppendLine("        string output,");
        builder.AppendLine("        int exitCode) =>");
        builder.AppendLine("        new(true, false, exitCode, string.Empty, output, command, new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal), []);");
    }

    private static void RenderDefaultApplication(
        StringBuilder builder,
        OpenConsoleDocument document)
    {
        builder.AppendLine();
        builder.AppendLine("    private static void ApplyDefaults(");
        builder.AppendLine("        string command,");
        builder.AppendLine("        Dictionary<string, List<string>> options,");
        builder.AppendLine("        Dictionary<string, int> occurrences)");
        builder.AppendLine("    {");
        builder.AppendLine("        switch (command)");
        builder.AppendLine("        {");
        foreach (var command in document.Commands
                     .OrderBy(static item => string.Join(" ", item.Path), StringComparer.Ordinal))
        {
            builder
                .Append("            case ")
                .Append(DotNetSourceText.CSharpLiteral(string.Join(" ", command.Path)))
                .AppendLine(":");
            builder.AppendLine("            {");
            foreach (var option in document.GlobalOptions
                         .Concat(command.Options)
                         .Where(static option => option.DefaultValue is not null))
            {
                builder
                    .Append("                if (!options.ContainsKey(")
                    .Append(DotNetSourceText.CSharpLiteral(option.LongName))
                    .AppendLine("))");
                builder.AppendLine("                {");
                builder
                    .Append("                    options.Add(")
                    .Append(DotNetSourceText.CSharpLiteral(option.LongName))
                    .Append(", [")
                    .Append(DotNetSourceText.CSharpLiteral(option.DefaultValue!))
                    .AppendLine("]);");
                builder
                    .Append("                    occurrences.TryAdd(")
                    .Append(DotNetSourceText.CSharpLiteral(option.LongName))
                    .AppendLine(", 0);");
                builder.AppendLine("                }");
            }

            builder.AppendLine("                break;");
            builder.AppendLine("            }");
        }

        builder.AppendLine("        }");
        builder.AppendLine("    }");
    }

    private static string BuildRootHelp(OpenConsoleDocument document)
    {
        var builder = new StringBuilder();
        builder.Append(document.Info.Name)
            .Append(' ')
            .Append(document.Info.Version.Value)
            .AppendLine()
            .AppendLine(document.Info.Summary)
            .AppendLine()
            .AppendLine("Commands:");
        foreach (var command in document.Commands
                     .OrderBy(static item => string.Join(" ", item.Path), StringComparer.Ordinal))
        {
            builder.Append("  ")
                .Append(string.Join(" ", command.Path))
                .Append("  ")
                .AppendLine(command.Summary);
        }

        builder.AppendLine()
            .Append("Use --")
            .Append(document.Help.LongOption)
            .AppendLine(" after a command for command help.");
        return builder.ToString().TrimEnd();
    }

    private static string BuildCommandHelp(
        OpenConsoleDocument document,
        OpenConsoleCommand command)
    {
        var builder = new StringBuilder();
        builder.Append("Usage: ")
            .Append(string.Join(" ", command.Path));
        foreach (var argument in command.Arguments)
        {
            builder.Append(argument.Required ? " <" : " [")
                .Append(argument.Name)
                .Append(argument.Required ? ">" : "]");
        }

        builder.AppendLine()
            .AppendLine(command.Summary);
        if (!command.Aliases.IsDefaultOrEmpty)
        {
            builder.Append("Aliases: ")
                .AppendLine(string.Join(
                    ", ",
                    command.Aliases.Select(static alias => string.Join(" ", alias))));
        }

        var options = document.GlobalOptions.Concat(command.Options).ToArray();
        if (options.Length > 0)
        {
            builder.AppendLine("Options:");
            foreach (var option in options.OrderBy(static item => item.LongName, StringComparer.Ordinal))
            {
                builder.Append("  --")
                    .Append(option.LongName);
                if (option.ShortName is not null)
                {
                    builder.Append(", -").Append(option.ShortName);
                }

                builder.Append("  ").AppendLine(option.Summary);
            }
        }

        builder.AppendLine("Exit codes:");
        foreach (var exitCode in command.ExitCodes.OrderBy(static item => item.Code))
        {
            builder.Append("  ")
                .Append(exitCode.Code.ToString(CultureInfo.InvariantCulture))
                .Append("  ")
                .AppendLine(exitCode.Meaning);
        }

        return builder.ToString().TrimEnd();
    }

    private static void RenderCommandOptionSwitch(
        StringBuilder builder,
        OpenConsoleDocument document,
        string method,
        Func<OpenConsoleOption, string> value,
        string fallback,
        string returnType = "bool")
    {
        builder.AppendLine();
        builder
            .Append("    private static ")
            .Append(returnType)
            .Append(' ')
            .Append(method)
            .AppendLine("(string command, string option) =>");
        builder.AppendLine("        string.Concat(command, \"\\u001f\", option) switch");
        builder.AppendLine("        {");
        foreach (var command in document.Commands.OrderBy(static item => string.Join(" ", item.Path), StringComparer.Ordinal))
        {
            var commandName = string.Join(" ", command.Path);
            foreach (var option in document.GlobalOptions.Concat(command.Options).DistinctBy(static item => item.LongName))
            {
                builder
                    .Append("            ")
                    .Append(DotNetSourceText.CSharpLiteral(string.Concat(commandName, "\u001f", option.LongName)))
                    .Append(" => ")
                    .Append(value(option))
                    .AppendLine(",");
            }
        }

        builder.Append("            _ => ").Append(fallback).AppendLine(",");
        builder.AppendLine("        };");
    }

    private static void RenderContractValidation(
        StringBuilder builder,
        OpenConsoleDocument document)
    {
        builder.AppendLine();
        builder.AppendLine("    private static string ValidateContract(");
        builder.AppendLine("        string command,");
        builder.AppendLine("        Dictionary<string, List<string>> options,");
        builder.AppendLine("        List<string> arguments)");
        builder.AppendLine("    {");
        builder.AppendLine("        switch (command)");
        builder.AppendLine("        {");
        foreach (var command in document.Commands.OrderBy(static item => string.Join(" ", item.Path), StringComparer.Ordinal))
        {
            builder
                .Append("            case ")
                .Append(DotNetSourceText.CSharpLiteral(string.Join(" ", command.Path)))
                .AppendLine(":");
            builder.AppendLine("            {");
            foreach (var option in document.GlobalOptions.Concat(command.Options).Where(static option => option.Required))
            {
                builder
                    .Append("                if (!options.ContainsKey(")
                    .Append(DotNetSourceText.CSharpLiteral(option.LongName))
                    .AppendLine("))");
                builder
                    .Append("                    return ")
                    .Append(DotNetSourceText.CSharpLiteral(string.Concat("PKNETC005 Required option missing: ", option.LongName)))
                    .AppendLine(";");
            }

            foreach (var option in command.Options)
            {
                foreach (var conflict in option.Conflicts)
                {
                    builder
                        .Append("                if (options.ContainsKey(")
                        .Append(DotNetSourceText.CSharpLiteral(option.LongName))
                        .Append(") && options.ContainsKey(")
                        .Append(DotNetSourceText.CSharpLiteral(conflict))
                        .AppendLine("))");
                    builder
                        .Append("                    return ")
                        .Append(DotNetSourceText.CSharpLiteral(string.Concat("PKNETC006 Conflicting options: ", option.LongName, ", ", conflict)))
                        .AppendLine(";");
                }

                foreach (var prerequisite in option.Prerequisites)
                {
                    builder
                        .Append("                if (options.ContainsKey(")
                        .Append(DotNetSourceText.CSharpLiteral(option.LongName))
                        .Append(") && !options.ContainsKey(")
                        .Append(DotNetSourceText.CSharpLiteral(prerequisite))
                        .AppendLine("))");
                    builder
                        .Append("                    return ")
                        .Append(DotNetSourceText.CSharpLiteral(string.Concat("PKNETC007 Prerequisite option missing: ", prerequisite)))
                        .AppendLine(";");
                }
            }

            RenderArgumentContractValidation(builder, command);
            builder.AppendLine("                break;");
            builder.AppendLine("            }");
        }

        builder.AppendLine("        }");
        builder.AppendLine();
        builder.AppendLine("        return string.Empty;");
        builder.AppendLine("    }");
    }

    private static void RenderArgumentContractValidation(
        StringBuilder builder,
        OpenConsoleCommand command)
    {
        var minimum = command.Arguments.Sum(static item => item.Occurrence.Minimum);
        var maximum = command.Arguments.Sum(static item => item.Occurrence.Maximum);
        builder
            .Append("                if (arguments.Count is < ")
            .Append(minimum)
            .Append(" or > ")
            .Append(maximum)
            .AppendLine(")");
        builder.AppendLine("                    return \"PKNETC008 Positional argument arity is invalid.\";");
        builder.AppendLine("                var argumentIndex = 0;");
        for (var index = 0; index < command.Arguments.Length; index++)
        {
            var argument = command.Arguments[index];
            var remainingMinimum = command.Arguments
                .Skip(index + 1)
                .Sum(static item => item.Occurrence.Minimum);
            builder
                .Append("                var argumentCount")
                .Append(index)
                .Append(" = Math.Min(")
                .Append(argument.Occurrence.Maximum)
                .Append(", Math.Max(")
                .Append(argument.Occurrence.Minimum)
                .Append(", arguments.Count - argumentIndex - ")
                .Append(remainingMinimum)
                .AppendLine("));");
            if (argument.DefaultValue is not null)
            {
                builder
                    .Append("                if (argumentCount")
                    .Append(index)
                    .AppendLine(" == 0)");
                builder.AppendLine("                {");
                builder
                    .Append("                    arguments.Insert(argumentIndex, ")
                    .Append(DotNetSourceText.CSharpLiteral(argument.DefaultValue))
                    .AppendLine(");");
                builder
                    .Append("                    argumentCount")
                    .Append(index)
                    .AppendLine(" = 1;");
                builder.AppendLine("                }");
            }

            builder
                .Append("                for (var offset = 0; offset < argumentCount")
                .Append(index)
                .AppendLine("; offset++)");
            builder.AppendLine("                {");
            builder
                .Append("                    if (!HasValidValueType(")
                .Append(DotNetSourceText.CSharpLiteral(argument.ValueType))
                .AppendLine(", arguments[argumentIndex + offset]))");
            builder
                .Append("                        return ")
                .Append(DotNetSourceText.CSharpLiteral(
                    string.Concat(
                        "PKNETC009 Invalid positional argument value: ",
                        argument.Name)))
                .AppendLine(";");
            builder.AppendLine("                }");
            builder
                .Append("                argumentIndex += argumentCount")
                .Append(index)
                .AppendLine(";");
        }

        builder.AppendLine("                if (argumentIndex != arguments.Count)");
        builder.AppendLine("                    return \"PKNETC008 Positional argument arity is invalid.\";");
    }
}
