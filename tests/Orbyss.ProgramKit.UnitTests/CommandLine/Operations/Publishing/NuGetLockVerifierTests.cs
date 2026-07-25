using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Publishing;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Publishing;

[TestClass]
public sealed class NuGetLockVerifierTests
{
    [TestMethod]
    public void VerifiesExactHostPackageVersionsDigestsAndContentHashes()
    {
        var hostLock = HostLock();
        var contentHash = Convert.ToBase64String(new byte[64]);
        var manifest = Manifest(hostLock, contentHash);
        NuGetLockVerifier sut = new(CreateSerializer());
        var accepted = LockBytes(hostLock, contentHash);
        var tampered = LockBytes(
            hostLock,
            Convert.ToBase64String(Enumerable.Repeat((byte)1, 64).ToArray()));

        sut.Verify(accepted, manifest, hostLock);
        Assert.ThrowsExactly<InvalidDataException>(
            () => sut.Verify(tampered, manifest, hostLock));
    }

    private static DotNetHostLock HostLock()
    {
        var shell = DotNetTestContractFactory.Shell();
        DotNetShellLockBuilder builder = new(
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator(),
                DotNetTestContractFactory.ProviderCatalog()));
        var document = builder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        return document.HostLocks.Single(static host =>
            host.Kind == DotNetHostKind.Api);
    }

    private static LocalPackageRootManifest Manifest(
        DotNetHostLock hostLock,
        string contentHash)
    {
        var input = new WorkspaceArtifactLocator(
            hostLock.InputVersionMapRevision,
            "version-map.json");
        var packages = hostLock.Packages
            .Select(package => new LocalPackageEntry(
                new ProgramKitIdentifier(string.Concat(
                    "pkid:project:tests:",
                    package.PackageId.Replace('.', '-')
                        .ToLowerInvariant())),
                string.Concat("src/", package.PackageId, ".csproj"),
                new ArtifactReference(
                    new ProgramKitIdentifier(string.Concat(
                        "pkid:package:tests:",
                        package.PackageId.Replace('.', '-')
                            .ToLowerInvariant())),
                    package.Version,
                    package.PackageDigest),
                package.PackageId,
                "program-kit",
                "net10.0",
                string.Concat(
                    package.PackageId,
                    ".",
                    package.Version.Value,
                    ".nupkg"),
                1,
                package.PackageDigest,
                contentHash,
                [],
                []))
            .ToImmutableArray();
        return new LocalPackageRootManifest(
            "pkid:schema:program-kit:local-package-root-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            ".",
            input,
            new WorkspaceArtifactLocator(
                hostLock.InputVersionSelectionRevision,
                "version-selection.json"),
            packages,
            []);
    }

    private static byte[] LockBytes(
        DotNetHostLock hostLock,
        string contentHash)
    {
        var libraries = hostLock.Packages.ToDictionary(
            static package => package.PackageId,
            package => (object)new Dictionary<string, object?>
            {
                ["type"] = "Direct",
                ["requested"] = string.Concat(
                    "[",
                    package.Version.Value,
                    ", ",
                    package.Version.Value,
                    "]"),
                ["resolved"] = package.Version.Value,
                ["contentHash"] = contentHash,
            },
            StringComparer.Ordinal);
        var document = new Dictionary<string, object?>
        {
            ["version"] = 1,
            ["dependencies"] = new Dictionary<string, object?>
            {
                [hostLock.Target.TargetFramework] = libraries,
            },
        };
        return JsonSerializer.SerializeToUtf8Bytes(document);
    }

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
