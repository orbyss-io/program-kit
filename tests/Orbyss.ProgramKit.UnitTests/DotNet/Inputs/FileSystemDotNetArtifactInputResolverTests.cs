using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Inputs;

[TestClass]
public sealed class FileSystemDotNetArtifactInputResolverTests
{
    [TestMethod]
    public async Task TraversalFailsBeforeAnyRead()
    {
        var revision = DotNetTestContractFactory.Ref("version-map", "inputs", 'a');
        var manifest = new DotNetArtifactInputManifest(
            "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            [new DotNetArtifactInputEntry(revision, "../outside.json")]);
        FileSystemDotNetArtifactInputResolver sut = new();

        var exception = await Assert.ThrowsExactlyAsync<DotNetKitException>(async () =>
            await sut.ResolveAsync(
                Path.GetTempPath(),
                manifest,
                revision,
                CancellationToken.None));

        Assert.AreEqual(DotNetDiagnosticIds.InvalidArtifactInput, exception.DiagnosticId);
    }

    [TestMethod]
    public async Task UnlistedRevisionFailsClosed()
    {
        var listed = DotNetTestContractFactory.Ref("version-map", "listed", 'a');
        var requested = DotNetTestContractFactory.Ref("version-map", "requested", 'b');
        var manifest = new DotNetArtifactInputManifest(
            "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            [new DotNetArtifactInputEntry(listed, "listed.json")]);
        FileSystemDotNetArtifactInputResolver sut = new();

        var exception = await Assert.ThrowsExactlyAsync<DotNetKitException>(async () =>
            await sut.ResolveAsync(
                Path.GetTempPath(),
                manifest,
                requested,
                CancellationToken.None));

        Assert.AreEqual(DotNetDiagnosticIds.InvalidArtifactInput, exception.DiagnosticId);
    }
}
