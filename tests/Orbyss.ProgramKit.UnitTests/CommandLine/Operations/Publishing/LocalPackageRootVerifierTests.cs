using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Publishing;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Publishing;

[TestClass]
public sealed class LocalPackageRootVerifierTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task RejectsUnlistedPackageBytesAndConflictingExternalIds()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-package-root-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var serializer = CreateSerializer();
            var packageBytes = "package"u8.ToArray();
            var packagePath = Path.Combine(root, "Local.Package.1.0.0.nupkg");
            await File.WriteAllBytesAsync(
                packagePath,
                packageBytes,
                TestContext.CancellationToken);
            var inputs = Reference("input", "1.0.0", 'a');
            var manifest = Manifest(packageBytes, inputs);
            var manifestPath = Path.Combine(
                root,
                "local-package-root-manifest.json");
            await WriteManifestAsync(
                serializer,
                manifestPath,
                manifest);
            LocalPackageRootVerifier sut = new(
                new CommandFileSystem(),
                serializer);

            _ = await sut.VerifyAsync(
                manifestPath,
                inputs,
                inputs,
                TestContext.CancellationToken);

            await File.WriteAllBytesAsync(
                packagePath,
                "tampered"u8.ToArray(),
                TestContext.CancellationToken);
            await Assert.ThrowsExactlyAsync<InvalidDataException>(
                async () => await sut.VerifyAsync(
                    manifestPath,
                    inputs,
                    inputs,
                    TestContext.CancellationToken));
            await File.WriteAllBytesAsync(
                packagePath,
                packageBytes,
                TestContext.CancellationToken);
            File.Delete(packagePath);
            await Assert.ThrowsExactlyAsync<InvalidDataException>(
                async () => await sut.VerifyAsync(
                    manifestPath,
                    inputs,
                    inputs,
                    TestContext.CancellationToken));
            await File.WriteAllBytesAsync(
                packagePath,
                packageBytes,
                TestContext.CancellationToken);

            await File.WriteAllBytesAsync(
                Path.Combine(root, "unlisted.nupkg"),
                "unexpected"u8.ToArray(),
                TestContext.CancellationToken);
            await Assert.ThrowsExactlyAsync<InvalidDataException>(
                async () => await sut.VerifyAsync(
                    manifestPath,
                    inputs,
                    inputs,
                    TestContext.CancellationToken));
            File.Delete(Path.Combine(root, "unlisted.nupkg"));

            var external = new LockedExternalPackage(
                Reference("external", "2.0.0", 'b'),
                "Local.Package",
                Convert.ToBase64String(new byte[64]),
                []);
            await WriteManifestAsync(
                serializer,
                manifestPath,
                manifest with { ExternalPackages = [external] });
            await Assert.ThrowsExactlyAsync<InvalidDataException>(
                async () => await sut.VerifyAsync(
                    manifestPath,
                    inputs,
                    inputs,
                    TestContext.CancellationToken));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private async Task WriteManifestAsync(
        ProgramKitJsonSerializer serializer,
        string path,
        LocalPackageRootManifest manifest)
    {
        var bytes = serializer.Write(
            manifest,
            CommandLineJsonProfiles.LocalOperations.Reference,
            CommandLineJsonProfiles.LocalOperations.MaximumLimits);
        await File.WriteAllBytesAsync(
            path,
            bytes.ToArray(),
            TestContext.CancellationToken);
    }

    private static LocalPackageRootManifest Manifest(
        ReadOnlySpan<byte> packageBytes,
        ArtifactReference inputs)
    {
        var locator = new WorkspaceArtifactLocator(inputs, "input.json");
        return new LocalPackageRootManifest(
            "pkid:schema:program-kit:local-package-root-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            ".",
            locator,
            locator,
            [
                new LocalPackageEntry(
                    new ProgramKitIdentifier("pkid:project:tests:local"),
                    "src/Local.Package.csproj",
                    Reference("local", "1.0.0", 'c'),
                    "Local.Package",
                    "program-kit",
                    "net10.0",
                    "Local.Package.1.0.0.nupkg",
                    packageBytes.Length,
                    new Sha256Digest(string.Concat(
                        "sha256:",
                        Convert.ToHexStringLower(
                            SHA256.HashData(packageBytes)))),
                    Convert.ToBase64String(SHA512.HashData(packageBytes)),
                    [],
                    []),
            ],
            []);
    }

    private static ArtifactReference Reference(
        string name,
        string version,
        char marker) =>
        new(
            new ProgramKitIdentifier(string.Concat("pkid:package:tests:", name)),
            new SemanticVersion(version),
            new Sha256Digest(string.Concat("sha256:", new string(marker, 64))));

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        LocalOperationsJsonProfileRegistration registration = new();
        registration.Register(builder);
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }
}
