using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Validation;

[TestClass]
public sealed class DotNetShellValidatorTests
{
    [TestMethod]
    public void ValidReviewedShellPasses()
    {
        DotNetShellValidator sut = new(new ArtifactReferenceValidator());

        var result = sut.Validate(DotNetTestContractFactory.Shell());

        Assert.IsTrue(result.IsValid);
    }

    [TestMethod]
    public void ProviderAbiDriftFailsWithStableDiagnostic()
    {
        var shell = DotNetTestContractFactory.Shell();
        shell = shell with
        {
            Composition = shell.Composition with
            {
                AbiVersion = new SemanticVersion("0.0.29"),
            },
        };
        DotNetShellValidator sut = new(new ArtifactReferenceValidator());

        var result = sut.Validate(shell);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Id == DotNetDiagnosticIds.InvalidShell));
    }

    [TestMethod]
    public void PortZeroFailsClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Api);
        var health = api.Health!;
        var listener = health.Listeners[0] with { Port = 0 };
        api = api with { Health = health with { Listeners = [listener] } };
        shell = shell with
        {
            Hosts = shell.Hosts.Select(host =>
                host.Kind == DotNetHostKind.Api ? api : host).ToImmutableArray(),
        };
        DotNetShellValidator sut = new(new ArtifactReferenceValidator());

        var result = sut.Validate(shell);

        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Id == DotNetDiagnosticIds.InvalidHealthConfiguration));
    }
}
