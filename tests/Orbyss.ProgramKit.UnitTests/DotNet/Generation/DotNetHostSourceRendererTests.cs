using System.Collections.Immutable;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Diagnostics;
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
    public void ApiAndWorkerKindsRetainExactCshellsComposition()
    {
        var shell = DotNetTestContractFactory.Shell();
        DotNetShellLockBuilder lockBuilder = new(CreateValidator());
        var lockDocument = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        var sut = CreateRenderer();

        foreach (var host in shell.Hosts.Where(static host =>
                     host.Kind != DotNetHostKind.Console))
        {
            var hostLock = lockDocument.HostLocks.Single(item =>
                item.HostIdentity == host.Identity);
            var outputs = sut.Render(
                host,
                hostLock,
                shell.Features,
                host.Kind == DotNetHostKind.Api
                    ? DotNetTestContractFactory.ApiDocument(shell)
                    : null);
            var project = Text(outputs, "GeneratedHost.csproj");
            var program = Text(
                outputs,
                "ProgramKitGenerated/Composition/Program.cs");

            Assert.Contains("Version=\"[0.0.28]\"", project);
            Assert.Contains(
                "OpenTelemetry.Extensions.Hosting\" Version=\"[1.17.0]\"",
                project);
            Assert.Contains(
                "typeof(global::Fixtures.SampleFeature)",
                program);
            Assert.Contains(
                "builder.Configuration.Sources.Clear()",
                program);
            Assert.Contains("ValidateOnStart()", program);
            if (host.Kind == DotNetHostKind.Api)
            {
                Assert.Contains("builder.AddShells", program);
                Assert.Contains("app.MapShells", program);
            }
            else
            {
                Assert.Contains("builder.Services.AddCShells", program);
                Assert.Contains("await host.RunAsync();", program);
            }
        }
    }

    [TestMethod]
    public void ConsoleKindRequiresDedicatedTypedGenerator()
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

        var exception = Assert.ThrowsExactly<DotNetKitException>(() =>
            CreateRenderer().Render(
                host,
                hostLock,
                shell.Features,
                null));

        Assert.AreEqual(
            DotNetDiagnosticIds.ConsoleProjectionFailed,
            exception.DiagnosticId);
    }

    [TestMethod]
    public void ApiAndWorkerShareGeneratedProjectVerificationTarget()
    {
        var shell = DotNetTestContractFactory.Shell();
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "reviewed",
            '7');
        DotNetShellLockBuilder lockBuilder =
            new(CreateValidator());
        var locks = lockBuilder.Build(shell, shellRevision);
        var sut = CreateRenderer();
        var targets = shell.Hosts
            .Where(static host => host.Kind != DotNetHostKind.Console)
            .Select(host => Text(
                sut.Render(
                    host,
                    locks.HostLocks.Single(candidate =>
                        candidate.HostIdentity == host.Identity),
                    shell.Features,
                    host.Kind == DotNetHostKind.Api
                        ? DotNetTestContractFactory.ApiDocument(shell)
                        : null),
                "Directory.Build.targets"))
            .ToArray();

        Assert.HasCount(2, targets);
        Assert.AreEqual(targets[0], targets[1]);
        Assert.Contains("ProgramKitVerifyGeneratedProject", targets[0]);
        Assert.Contains(
            "ProgramKitCSharpGateGeneratedProjectBinding>1.0.0",
            targets[0]);
        Assert.Contains(
            "DependsOnTargets=\"ProgramKitConfigureGeneratedProjectVerification;Build\"",
            targets[0]);
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
        var document =
            DotNetTestContractFactory.ApiDocument(fastEndpointsShell);
        var sut = CreateRenderer();

        var baseline = sut.Render(
            baselineHost,
            baselineLock.HostLocks.Single(static item =>
                item.Kind == DotNetHostKind.Api),
            baselineShell.Features,
            document);
        var projected = sut.Render(
            fastEndpointsHost,
            fastEndpointsLock.HostLocks.Single(static item =>
                item.Kind == DotNetHostKind.Api),
            fastEndpointsShell.Features,
            document);

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
    }

    private static DotNetShellValidator CreateValidator() =>
        new DotNetShellValidator(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());

    private static DotNetHostSourceRenderer CreateRenderer() =>
        new(
            new DotNetConfigurationProjectionCompiler(
                DotNetTestContractFactory.ProviderRegistry()),
            new DotNetTelemetryProjectionCompiler(),
            new DotNetTransportFailureProjectionCompiler(),
            new DotNetSecurityProjectionCompiler(),
            new Orbyss.ProgramKit.DotNet.Generation.FastEndpoints.DotNetFastEndpointsProjectionCompiler());

    private static string Text(
        ImmutableArray<Orbyss.ProgramKit.Workbench.Operations.Generation.GeneratedOutput> outputs,
        string relativePath) =>
        Encoding.UTF8.GetString(
            outputs.Single(output =>
                output.RelativePath == relativePath).Content.Span);
}
