using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Inputs;

[TestClass]
public sealed class FileSystemDotNetArtifactInputResolverTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task ExactInputReturnsItsVerifiedContainedPhysicalPath()
    {
        var root = Directory.CreateTempSubdirectory(
            "program-kit-resolved-input-");
        try
        {
            var bytes = "{}"u8.ToArray();
            var path = Path.Combine(root.FullName, "input.json");
            await File.WriteAllBytesAsync(
                path,
                bytes,
                TestContext.CancellationToken);
            var revision = new ArtifactReference(
                DotNetTestContractFactory.Id("input", "verified"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    string.Concat(
                        "sha256:",
                        Convert.ToHexStringLower(
                            System.Security.Cryptography.SHA256.HashData(
                                bytes)))));
            var manifest = new DotNetArtifactInputManifest(
                "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
                new SemanticVersion("1.0.0"),
                [new DotNetArtifactInputEntry(revision, "input.json")],
                []);
            FileSystemDotNetArtifactInputResolver sut = new();

            var result = await sut.ResolveAsync(
                root.FullName,
                manifest,
                revision,
                TestContext.CancellationToken);

            Assert.AreEqual(Path.GetFullPath(path), result.FullPath);
            Assert.AreEqual("input.json", result.RelativePath);
            Assert.AreSequenceEqual(bytes, result.Content.ToArray());
        }
        finally
        {
            root.Delete(recursive: true);
        }
    }

    [TestMethod]
    public async Task TraversalFailsBeforeAnyRead()
    {
        var revision = DotNetTestContractFactory.Ref("version-map", "inputs", 'a');
        var manifest = new DotNetArtifactInputManifest(
            "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            [new DotNetArtifactInputEntry(revision, "../outside.json")],
            []);
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
            [new DotNetArtifactInputEntry(listed, "listed.json")],
            []);
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
