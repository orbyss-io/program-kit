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
            new DotNetShellValidator(new ArtifactReferenceValidator());
        DotNetShellLockBuilder lockBuilder = new(validator);
        var lockDocument = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        DotNetHostSourceRenderer sut = new();

        foreach (var host in shell.Hosts)
        {
            var hostLock = lockDocument.HostLocks.Single(item =>
                item.HostIdentity == host.Identity);
            var console = host.Kind == DotNetHostKind.Console
                ? DotNetTestContractFactory.ConsoleDocument(shell)
                : null;
            var outputs = sut.Render(host, hostLock, shell.Features, console);
            var project = Text(outputs, "GeneratedHost.csproj");
            var buildTargets = Text(outputs, "Directory.Build.targets");
            var packagePolicy = Text(outputs, "Directory.Packages.props");
            var program = Text(outputs, "ProgramKitGenerated/Composition/Program.cs");

            Assert.Contains("Version=\"[0.0.28]\"", project);
            Assert.AreEqual("<Project />", buildTargets.Trim());
            Assert.AreEqual("<Project />", packagePolicy.Trim());
            Assert.Contains("typeof(global::Fixtures.SampleFeature)", program);
            Assert.IsFalse(project.Contains("Orbyss.ProgramKit.DotNet", StringComparison.Ordinal));
            Assert.IsFalse(project.Contains("Orbyss.ProgramKit.Workbench", StringComparison.Ordinal));
            if (host.Kind == DotNetHostKind.Api)
            {
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
            new DotNetShellValidator(new ArtifactReferenceValidator());
        DotNetShellLockBuilder lockBuilder = new(validator);
        var locks = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Console);
        var hostLock = locks.HostLocks.Single(static item => item.Kind == DotNetHostKind.Console);
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        DotNetHostSourceRenderer sut = new();

        var outputs = sut.Render(host, hostLock, shell.Features, document);
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

    private static string Text(
        ImmutableArray<Orbyss.ProgramKit.Workbench.Operations.Generation.GeneratedOutput> outputs,
        string path) =>
        Encoding.UTF8.GetString(
            outputs.Single(item => item.RelativePath == path).Content.Span);
}
