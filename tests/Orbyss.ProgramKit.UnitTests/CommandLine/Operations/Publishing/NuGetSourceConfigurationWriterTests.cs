using System.Text;
using System.Xml.Linq;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Publishing;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Publishing;

[TestClass]
public sealed class NuGetSourceConfigurationWriterTests
{
    private static readonly string[] FirstPartyPackages =
        ["Local.Package"];

    private static readonly string[] ExternalPackages =
        ["External.Package"];

    [TestMethod]
    public void WritesOnlyExactDisjointPackageMappings()
    {
        NuGetSourceConfigurationWriter sut = new();

        var bytes = sut.Write(
            Path.GetTempPath(),
            Manifest());
        var document = XDocument.Parse(Encoding.UTF8.GetString(bytes.Span));
        var mappings = document
            .Descendants("packageSource")
            .ToDictionary(
                element => element.Attribute("key")!.Value,
                element => element
                    .Elements("package")
                    .Select(package => package.Attribute("pattern")!.Value)
                    .ToArray(),
                StringComparer.Ordinal);

        Assert.AreSequenceEqual(
            FirstPartyPackages,
            mappings["first-party"]);
        Assert.AreSequenceEqual(
            ExternalPackages,
            mappings["nuget.org"]);
        Assert.IsFalse(document.ToString().Contains('*', StringComparison.Ordinal));
        Assert.AreEqual(
            "https://api.nuget.org/v3/index.json",
            document
                .Descendants("packageSources")
                .Elements("add")
                .Single(element =>
                    element.Attribute("key")!.Value == "nuget.org")
                .Attribute("value")!
                .Value);
    }

    private static LocalPackageRootManifest Manifest()
    {
        var revision = Reference("local", "0.1.0-alpha.1", 'a');
        var input = new WorkspaceArtifactLocator(
            Reference("input", "1.0.0", 'b'),
            "input.json");
        return new LocalPackageRootManifest(
            "pkid:schema:program-kit:local-package-root-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            ".",
            input,
            input,
            [
                new LocalPackageEntry(
                    new ProgramKitIdentifier("pkid:project:tests:local"),
                    "src/Local.Package.csproj",
                    revision,
                    "Local.Package",
                    "program-kit",
                    "net10.0",
                    "packages/Local.Package.0.1.0-alpha.1.nupkg",
                    1,
                    revision.Digest,
                    Convert.ToBase64String(new byte[64]),
                    [],
                    []),
            ],
            [
                new LockedExternalPackage(
                    Reference("external", "2.0.0", 'c'),
                    "External.Package",
                    Convert.ToBase64String(new byte[64]),
                    []),
            ]);
    }

    private static ArtifactReference Reference(
        string name,
        string version,
        char marker) =>
        new(
            new ProgramKitIdentifier(string.Concat("pkid:package:tests:", name)),
            new SemanticVersion(version),
            new Sha256Digest(string.Concat("sha256:", new string(marker, 64))));
}
