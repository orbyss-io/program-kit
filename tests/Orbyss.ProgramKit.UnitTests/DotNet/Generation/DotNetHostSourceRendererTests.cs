using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetHostSourceRendererTests
{
    [TestMethod]
    public void AllKindsRenderExactTargetAndDirectCshellsComposition()
    {
        var shell = DotNetTestContractFactory.Shell();
        IDotNetShellValidator validator =
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator(),
                new TransportFailureProfileValidator(),
                new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
                DotNetTestContractFactory.ProviderCatalog());
        DotNetShellLockBuilder lockBuilder = new(validator);
        var lockDocument = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        DotNetHostSourceRenderer sut =
            new(new DotNetConfigurationProjectionCompiler(
                    DotNetTestContractFactory.ProviderRegistry()),
                new DotNetTelemetryProjectionCompiler(),
                new DotNetTransportFailureProjectionCompiler(),
                new DotNetSecurityProjectionCompiler(),
                new Orbyss.ProgramKit.DotNet.Generation.FastEndpoints.DotNetFastEndpointsProjectionCompiler());

        foreach (var host in shell.Hosts)
        {
            var hostLock = lockDocument.HostLocks.Single(item =>
                item.HostIdentity == host.Identity);
            var console = host.Kind == DotNetHostKind.Console
                ? DotNetTestContractFactory.ConsoleDocument(shell)
                : null;
            var outputs = sut.Render(
                host,
                hostLock,
                shell.Features,
                null,
                console);
            var project = Text(outputs, "GeneratedHost.csproj");
            var buildTargets = Text(outputs, "Directory.Build.targets");
            var packagePolicy = Text(outputs, "Directory.Packages.props");
            var program = Text(outputs, "ProgramKitGenerated/Composition/Program.cs");
            var options = Text(
                outputs,
                "ProgramKitGenerated/Configuration/SampleClientOptions.cs");
            var optionsValidator = Text(
                outputs,
                "ProgramKitGenerated/Configuration/SampleClientOptionsValidator.cs");
            var telemetry = Text(
                outputs,
                "ProgramKitGenerated/Hosting/ProgramKitTelemetry.cs");
            var telemetryOptions = Text(
                outputs,
                "ProgramKitGenerated/Hosting/ProgramKitTelemetryOptions.cs");

            Assert.Contains("Version=\"[0.0.28]\"", project);
            Assert.Contains(
                "OpenTelemetry.Extensions.Hosting\" Version=\"[1.17.0]\"",
                project);
            Assert.AreEqual("<Project />", buildTargets.Trim());
            Assert.AreEqual("<Project />", packagePolicy.Trim());
            Assert.Contains("typeof(global::Fixtures.SampleFeature)", program);
            Assert.Contains("builder.Configuration.Sources.Clear()", program);
            Assert.Contains("AddJsonFile(\"appsettings.json\"", program);
            Assert.Contains("AddOptions<global::GeneratedHost.Configuration.SampleClientOptions>", program);
            Assert.Contains("[OptionsValidator]", optionsValidator);
            Assert.Contains("[Required]", options);
            Assert.Contains("[LoggerMessage(EventId = 1001", telemetry);
            Assert.Contains(
                "public Uri Endpoint",
                telemetryOptions);
            Assert.Contains(
                "ProgramKitTelemetryOptions.ParseEndpoint",
                program);
            Assert.Contains("ValidateOnStart()", program);
            Assert.Contains(
                "<EnableConfigurationBindingGenerator>true</EnableConfigurationBindingGenerator>",
                project);
            Assert.IsFalse(project.Contains("Orbyss.ProgramKit.DotNet", StringComparison.Ordinal));
            Assert.IsFalse(project.Contains("Orbyss.ProgramKit.Workbench", StringComparison.Ordinal));
            if (host.Kind == DotNetHostKind.Api)
            {
                Assert.Contains("options.CombineLogs = true", program);
                Assert.Contains(
                    "\"Microsoft.AspNetCore.Hosting.Diagnostics\"",
                    program);
                Assert.Contains("builder.AddShells", program);
                Assert.Contains("app.MapShells", program);
                Assert.Contains("context.Connection.LocalPort", program);
            }
            else
            {
                Assert.Contains("builder.Services.AddCShells", program);
            }
        }
    }

    [TestMethod]
    public void ConsoleParserIsGeneratedFromTheSameFrozenDescriptor()
    {
        var shell = DotNetTestContractFactory.Shell();
        IDotNetShellValidator validator =
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator(),
                new TransportFailureProfileValidator(),
                new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
                DotNetTestContractFactory.ProviderCatalog());
        DotNetShellLockBuilder lockBuilder = new(validator);
        var locks = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Console);
        var hostLock = locks.HostLocks.Single(static item => item.Kind == DotNetHostKind.Console);
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        DotNetHostSourceRenderer sut =
            new(new DotNetConfigurationProjectionCompiler(
                    DotNetTestContractFactory.ProviderRegistry()),
                new DotNetTelemetryProjectionCompiler(),
                new DotNetTransportFailureProjectionCompiler(),
                new DotNetSecurityProjectionCompiler(),
                new Orbyss.ProgramKit.DotNet.Generation.FastEndpoints.DotNetFastEndpointsProjectionCompiler());

        var outputs = sut.Render(
            host,
            hostLock,
            shell.Features,
            null,
            document);
        var parser = Text(
            outputs,
            "ProgramKitGenerated/Commands/GeneratedConsoleParser.cs");

        Assert.Contains("\"observe\", \"run\"", parser);
        Assert.Contains("\"execute\"", parser);
        Assert.Contains("\"run-observation\"", parser);
        Assert.Contains("\"--count\"", parser);
        Assert.Contains("\"--number\"", parser);
        Assert.Contains("--count=<int32>", parser);
        Assert.Contains("CultureInfo.InvariantCulture", parser);
        Assert.Contains("token == \"--\"", parser);
        Assert.Contains("ApplyDefaults", parser);
        Assert.Contains("MinimumValues", parser);
        Assert.Contains("MaximumValues", parser);
        Assert.Contains("RenderHelp", parser);
        Assert.Contains("CompletionCandidates", parser);
        Assert.Contains("PKNETC009", parser);
        Assert.Contains("PKNETC006", parser);
        Assert.Contains("PKNETC007", parser);
    }

    [TestMethod]
    public void ConsoleDispatchContractAndLifecycleAreExactForGenericAndWebHosts()
    {
        var shell = DotNetTestContractFactory.Shell();
        DotNetShellLockBuilder lockBuilder = new(CreateValidator());
        var locks = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        var consoleHost = shell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Console);
        var consoleLock = locks.HostLocks.Single(static item =>
            item.Kind == DotNetHostKind.Console);
        var apiHealth = shell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Api).Health;
        var renderer = CreateRenderer();

        foreach (var host in new[]
                 {
                     consoleHost,
                     consoleHost with
                     {
                         Health = apiHealth,
                     },
                 })
        {
            var outputs = renderer.Render(
                host,
                consoleLock,
                shell.Features,
                null,
                DotNetTestContractFactory.ConsoleDocument(shell));
            var contract = Text(
                outputs,
                "ProgramKitGenerated/Commands/IProgramKitConsoleCommandDispatcher.cs");
            var program = Text(
                outputs,
                "ProgramKitGenerated/Composition/Program.cs");

            Assert.AreEqual(
                """
                namespace GeneratedHost.Commands;

                internal interface IProgramKitConsoleCommandDispatcher
                {
                    ValueTask<int> DispatchAsync(
                        GeneratedConsoleParseResult parseResult,
                        CancellationToken cancellationToken);
                }

                """.Replace("\r\n", "\n", StringComparison.Ordinal),
                contract);
            Assert.Contains(
                "static partial void ConfigureProgramKitConsoleServices(",
                program);
            Assert.Contains(
                "ConfigureProgramKitConsoleServices(builder.Services);",
                program);
            Assert.Contains(
                ".GetServices<GeneratedHost.Commands.IProgramKitConsoleCommandDispatcher>()",
                program);
            Assert.Contains("if (dispatchers.Length != 1)", program);
            Assert.Contains("await dispatcher.DispatchAsync(", program);
            Assert.Contains(
                "applicationLifetime.ApplicationStopping",
                program);
            Assert.Contains("TimeSpan.FromSeconds(30)", program);
            Assert.DoesNotContain("await host.RunAsync();", program);
            Assert.DoesNotContain("await app.RunAsync();", program);
            Assert.DoesNotContain("return 0;", program);
            AssertOccursBefore(
                program,
                "GeneratedConsoleParser.Parse(args)",
                host.Health is null
                    ? "Host.CreateApplicationBuilder(args)"
                    : "WebApplication.CreateBuilder(args)");
            AssertOccursBefore(
                program,
                "ConfigureProgramKitConsoleServices(builder.Services);",
                host.Health is null
                    ? "using var host = builder.Build();"
                    : "await using var app = builder.Build();");
            AssertOccursBefore(
                program,
                "if (dispatchers.Length != 1)",
                ".StartAsync();");
            AssertOccursBefore(
                program,
                ".StartAsync();",
                "dispatcher.DispatchAsync(");
            AssertOccursBefore(
                program,
                "dispatcher.DispatchAsync(",
                ".StopAsync(stopCancellation.Token);");
            Assert.Contains(
                host.Health is null
                    ? "Host.CreateApplicationBuilder(args)"
                    : "WebApplication.CreateBuilder(args)",
                program);
        }
    }

    [TestMethod]
    public void CurrentConsoleParserAndParseResultBytesMatchGoldenDigests()
    {
        var shell = DotNetTestContractFactory.Shell();
        DotNetShellLockBuilder lockBuilder = new(CreateValidator());
        var locks = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        var host = shell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Console);
        var hostLock = locks.HostLocks.Single(static item =>
            item.Kind == DotNetHostKind.Console);

        var outputs = CreateRenderer().Render(
            host,
            hostLock,
            shell.Features,
            null,
            DotNetTestContractFactory.ConsoleDocument(shell));

        Assert.AreEqual(
            "sha256:2e4434b1df81274c2d8d5a41911d7a23a837b5db63da93687aed6b1862538ec3",
            Digest(outputs, "ProgramKitGenerated/Commands/GeneratedConsoleParser.cs"));
        Assert.AreEqual(
            "sha256:a95b7bf78aea54d000c580e033faca7638b66accbe87ee7e8a7e9ebc734d1f61",
            Digest(outputs, "ProgramKitGenerated/Commands/GeneratedConsoleParseResult.cs"));
    }

    [TestMethod]
    public void FastEndpointsAddsOnlyPinnedSyntaxAdapterAndPreservesOwners()
    {
        var baselineShell = DotNetTestContractFactory.Shell();
        var fastEndpointsShell =
            DotNetTestContractFactory.WithFastEndpoints(baselineShell);
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "reviewed",
            '7');
        DotNetShellLockBuilder lockBuilder = new(CreateValidator());
        var baselineLock = lockBuilder.Build(
            baselineShell,
            shellRevision);
        var fastEndpointsLock = lockBuilder.Build(
            fastEndpointsShell,
            shellRevision);
        var baselineHost = baselineShell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Api);
        var fastEndpointsHost = fastEndpointsShell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Api);
        var baselineHostLock = baselineLock.HostLocks.Single(static item =>
            item.Kind == DotNetHostKind.Api);
        var fastEndpointsHostLock = fastEndpointsLock.HostLocks.Single(
            static item => item.Kind == DotNetHostKind.Api);
        var document =
            DotNetTestContractFactory.ApiDocument(fastEndpointsShell);
        var sut = CreateRenderer();

        var baseline = sut.Render(
            baselineHost,
            baselineHostLock,
            baselineShell.Features,
            document,
            null);
        var projected = sut.Render(
            fastEndpointsHost,
            fastEndpointsHostLock,
            fastEndpointsShell.Features,
            document,
            null);

        var ownerPaths = baseline
            .Select(static output => output.RelativePath)
            .Where(static path =>
                path.Contains(
                    "ProgramKitOperationAuthorizationMiddleware.cs",
                    StringComparison.Ordinal) ||
                path.Contains(
                    "ProgramKitMappedTransportFailureHandler.cs",
                    StringComparison.Ordinal) ||
                path.Contains(
                    "ProgramKitFallbackTransportFailureHandler.cs",
                    StringComparison.Ordinal) ||
                path.Contains(
                    "ProgramKitProblemDetailsWriter.cs",
                    StringComparison.Ordinal))
            .ToArray();
        Assert.IsNotEmpty(ownerPaths);
        foreach (var path in ownerPaths)
        {
            Assert.AreSequenceEqual(
                baseline.Single(output =>
                    output.RelativePath == path).Content.ToArray(),
                projected.Single(output =>
                    output.RelativePath == path).Content.ToArray());
        }

        var project = Text(projected, "GeneratedHost.csproj");
        var program = Text(
            projected,
            "ProgramKitGenerated/Composition/Program.cs");
        Assert.Contains(
            "CShells.FastEndpoints\" Version=\"[0.0.28]\"",
            project);
        Assert.Contains(
            "FastEndpoints\" Version=\"[7.2.0]\"",
            project);
        Assert.Contains(
            "GeneratedHost.Hosting.ProgramKitFastEndpointsFeature",
            program);
        Assert.Contains("app.UseExceptionHandler", program);
        Assert.Contains(
            "ProgramKitOperationAuthorizationMiddleware",
            program);
        Assert.IsTrue(projected.Any(static output =>
            output.RelativePath ==
                "ProgramKitGenerated/Hosting/IProgramKitFastEndpointOperationDispatcher.cs"));
        Assert.IsTrue(projected.Any(static output =>
            output.RelativePath ==
                "ProgramKitGenerated/Hosting/ProgramKitFastEndpointsFeature.cs"));
        Assert.IsTrue(projected.Any(static output =>
            output.RelativePath.StartsWith(
                "ProgramKitGenerated/Hosting/ProgramKitFastEndpoint",
                StringComparison.Ordinal)));
        Assert.IsTrue(projected.Any(static output =>
            output.RelativePath ==
                "ProgramKitGenerated/Hosting/fastendpoints-projection.json"));
        Assert.IsFalse(baseline.Any(static output =>
            output.RelativePath.Contains(
                "FastEndpoint",
                StringComparison.Ordinal)));
    }

    private static DotNetHostSourceRenderer CreateRenderer() =>
        new(
            new DotNetConfigurationProjectionCompiler(
                DotNetTestContractFactory.ProviderRegistry()),
            new DotNetTelemetryProjectionCompiler(),
            new DotNetTransportFailureProjectionCompiler(),
            new DotNetSecurityProjectionCompiler(),
            new Orbyss.ProgramKit.DotNet.Generation.FastEndpoints.DotNetFastEndpointsProjectionCompiler());

    private static DotNetShellValidator CreateValidator() =>
        new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());

    private static string Text(
        ImmutableArray<Orbyss.ProgramKit.Workbench.Operations.Generation.GeneratedOutput> outputs,
        string path) =>
        Encoding.UTF8.GetString(
            outputs.Single(item => item.RelativePath == path).Content.Span);

    private static string Digest(
        ImmutableArray<Orbyss.ProgramKit.Workbench.Operations.Generation.GeneratedOutput> outputs,
        string path) =>
        string.Concat(
            "sha256:",
            Convert.ToHexStringLower(
                SHA256.HashData(
                    outputs.Single(item =>
                        item.RelativePath == path).Content.Span)));

    private static void AssertOccursBefore(
        string content,
        string expectedBefore,
        string expectedAfter)
    {
        var beforeIndex = content.IndexOf(
            expectedBefore,
            StringComparison.Ordinal);
        var afterIndex = content.IndexOf(
            expectedAfter,
            StringComparison.Ordinal);
        Assert.IsTrue(
            beforeIndex >= 0 && afterIndex > beforeIndex,
            string.Concat(
                "'",
                expectedBefore,
                "' must occur before '",
                expectedAfter,
                "'."));
    }
}
