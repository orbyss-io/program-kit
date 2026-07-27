using System.Collections.Immutable;
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
}
