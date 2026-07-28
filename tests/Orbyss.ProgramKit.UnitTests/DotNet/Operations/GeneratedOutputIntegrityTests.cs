using System.Security.Cryptography;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Publication;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Sealing;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Operations;

[TestClass]
public sealed class GeneratedOutputIntegrityTests
{
    [TestMethod]
    public void SealIsByteDeterministicAndOrdinallyOrdered()
    {
        GeneratedOutputSealer sut = new();
        GeneratedOutputPayload[] payloads =
        [
            new("zeta.txt", "zeta"u8.ToArray()),
            new("ProgramKitGenerated/Program.cs", "program"u8.ToArray()),
        ];

        var first = sut.Seal(payloads);
        var second = sut.Seal(payloads.Reverse());

        Assert.AreSequenceEqual(
            first.ManifestBytes.ToArray(),
            second.ManifestBytes.ToArray());
        Assert.AreSequenceEqual(
            first.AnchorBytes.ToArray(),
            second.AnchorBytes.ToArray());
        Assert.AreEqual(
            "ProgramKitGenerated/Program.cs",
            first.Manifest.Files[0].Path);
        Assert.AreEqual("zeta.txt", first.Manifest.Files[1].Path);
    }

    [TestMethod]
    public void NeutralSchemasAreEmbeddedAtTheirExactApprovedDigests()
    {
        var assembly = typeof(GeneratedOutputManifest).Assembly;

        AssertEmbeddedDigest(
            assembly,
            "Orbyss.ProgramKit.GeneratedOutputIntegrity.Schemas.generated-output-manifest-1.0.0.schema.json",
            GeneratedOutputIntegrityConstants.ManifestSchemaSha256);
        AssertEmbeddedDigest(
            assembly,
            "Orbyss.ProgramKit.GeneratedOutputIntegrity.Schemas.generated-output-anchor-1.0.0.schema.json",
            GeneratedOutputIntegrityConstants.AnchorSchemaSha256);
    }

    [TestMethod]
    public async Task PublishThenVerifyPassesAndOutsideConsumerFilesAreIgnored()
    {
        using TemporaryDirectory temporary = new();
        var root = Path.Combine(temporary.Path, "Product.Cli.Host");
        var sut = Publisher();

        await sut.PublishCreateAsync(
            root,
            Payloads(),
            CancellationToken.None);
        await File.WriteAllTextAsync(
            Path.Combine(temporary.Path, "consumer-owned.targets"),
            "consumer",
            CancellationToken.None);

        var result = await Verifier().VerifyAsync(
            root,
            CancellationToken.None);

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Issues.Select(static issue => issue.Message)));
        Assert.IsTrue(File.Exists(
            GeneratedOutputPathPolicy.AnchorPath(root)));
        Assert.IsTrue(File.Exists(
            GeneratedOutputPathPolicy.ResolveUnderRoot(
                root,
                GeneratedOutputIntegrityConstants.ManifestRelativePath,
                allowManifest: true)));
    }

    [TestMethod]
    public async Task ModifiedMissingAndUnexpectedFilesAreAllReportedAsTampering()
    {
        using TemporaryDirectory temporary = new();
        var root = Path.Combine(temporary.Path, "Product.Cli.Host");
        await Publisher().PublishCreateAsync(
            root,
            Payloads(),
            CancellationToken.None);
        await File.WriteAllTextAsync(
            Path.Combine(root, "Program.cs"),
            "changEd",
            CancellationToken.None);
        File.Delete(Path.Combine(root, "Generated", "Command.cs"));
        await File.WriteAllTextAsync(
            Path.Combine(root, "Generated", "Injected.cs"),
            "injected",
            CancellationToken.None);

        var result = await Verifier().VerifyAsync(
            root,
            CancellationToken.None);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Issues.Any(static issue =>
            issue.Kind == GeneratedOutputIntegrityIssueKind.Modified &&
            issue.Path == "Program.cs"));
        Assert.IsTrue(result.Issues.Any(static issue =>
            issue.Kind == GeneratedOutputIntegrityIssueKind.Missing &&
            issue.Path == "Generated/Command.cs"));
        Assert.IsTrue(result.Issues.Any(static issue =>
            issue.Kind == GeneratedOutputIntegrityIssueKind.Unexpected &&
            issue.Path == "Generated/Injected.cs"));
        Assert.IsTrue(result.Issues.All(static issue =>
            issue.Message.StartsWith(
                "Tampered-with Program Kit generated output:",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public async Task MissingOrMismatchedExternalAnchorFailsClosed()
    {
        using TemporaryDirectory temporary = new();
        var root = Path.Combine(temporary.Path, "Product.Cli.Host");
        await Publisher().PublishCreateAsync(
            root,
            Payloads(),
            CancellationToken.None);
        var anchor = GeneratedOutputPathPolicy.AnchorPath(root);
        File.Delete(anchor);

        var missing = await Verifier().VerifyAsync(
            root,
            CancellationToken.None);
        Assert.AreEqual(
            GeneratedOutputIntegrityIssueKind.Unsealed,
            missing.Issues.Single().Kind);

        await File.WriteAllTextAsync(
            anchor,
            """
            {
              "$schema": "pkid:schema:program-kit:generated-output-anchor@1.0.0",
              "formatVersion": "1.0.0",
              "manifestPath": ".program-kit/generated-output.manifest.json",
              "manifestSha256": "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            }
            """,
            CancellationToken.None);
        var mismatch = await Verifier().VerifyAsync(
            root,
            CancellationToken.None);
        Assert.AreEqual(
            GeneratedOutputIntegrityIssueKind.Unsealed,
            mismatch.Issues.Single().Kind);
    }

    [TestMethod]
    public async Task MalformedManifestIsReportedAfterItsExactBytesAreSealed()
    {
        using TemporaryDirectory temporary = new();
        var root = Path.Combine(temporary.Path, "Product.Cli.Host");
        await Publisher().PublishCreateAsync(
            root,
            Payloads(),
            CancellationToken.None);
        var malformed = "{ \"not\": \"a manifest\" }\n"u8.ToArray();
        var manifest = GeneratedOutputPathPolicy.ResolveUnderRoot(
            root,
            GeneratedOutputIntegrityConstants.ManifestRelativePath,
            allowManifest: true);
        await File.WriteAllBytesAsync(
            manifest,
            malformed,
            CancellationToken.None);
        GeneratedOutputSealer sealer = new();
        await File.WriteAllBytesAsync(
            GeneratedOutputPathPolicy.AnchorPath(root),
            sealer.CreateAnchorBytes(malformed).ToArray(),
            CancellationToken.None);

        var result = await Verifier().VerifyAsync(
            root,
            CancellationToken.None);

        Assert.AreEqual(
            GeneratedOutputIntegrityIssueKind.Malformed,
            result.Issues.Single().Kind);
        Assert.Contains(
            "Tampered-with Program Kit generated output",
            result.Issues.Single().Message);
    }

    [TestMethod]
    public void UnsafeAndReservedPayloadPathsFailBeforeFilesystemMutation()
    {
        GeneratedOutputSealer sut = new();

        Assert.ThrowsExactly<InvalidDataException>(
            () => sut.Seal(
                [new("../escape.cs", "x"u8.ToArray())]));
        Assert.ThrowsExactly<InvalidDataException>(
            () => sut.Seal(
                [
                    new(
                        GeneratedOutputIntegrityConstants.ManifestRelativePath,
                        "x"u8.ToArray()),
                ]));
        Assert.ThrowsExactly<InvalidDataException>(
            () => sut.Seal(
                [new("Generated/CON.cs", "x"u8.ToArray())]));
    }

    [TestMethod]
    public async Task ReadyTransactionRecoversTheExternalAnchorWithoutRegeneration()
    {
        using TemporaryDirectory temporary = new();
        var root = Path.Combine(temporary.Path, "Product.Cli.Host");
        var transaction = GeneratedOutputPathPolicy.TransactionPath(root);
        Directory.CreateDirectory(transaction);
        Directory.CreateDirectory(root);
        var payloads = Payloads();
        GeneratedOutputSealer sealer = new();
        var seal = sealer.Seal(payloads);
        foreach (var payload in payloads)
        {
            var path = GeneratedOutputPathPolicy.ResolveUnderRoot(
                root,
                payload.RelativePath);
            Directory.CreateDirectory(
                Path.GetDirectoryName(path) ??
                throw new InvalidOperationException());
            await File.WriteAllBytesAsync(
                path,
                payload.Content.ToArray(),
                CancellationToken.None);
        }

        var manifestPath = GeneratedOutputPathPolicy.ResolveUnderRoot(
            root,
            GeneratedOutputIntegrityConstants.ManifestRelativePath,
            allowManifest: true);
        Directory.CreateDirectory(
            Path.GetDirectoryName(manifestPath) ??
            throw new InvalidOperationException());
        await File.WriteAllBytesAsync(
            manifestPath,
            seal.ManifestBytes.ToArray(),
            CancellationToken.None);
        await File.WriteAllBytesAsync(
            Path.Combine(transaction, "anchor.json"),
            seal.AnchorBytes.ToArray(),
            CancellationToken.None);
        await File.WriteAllTextAsync(
            Path.Combine(transaction, "ready"),
            "ready\n",
            CancellationToken.None);

        await Publisher().RecoverAsync(
            root,
            CancellationToken.None);

        Assert.IsFalse(Directory.Exists(transaction));
        Assert.IsTrue(File.Exists(
            GeneratedOutputPathPolicy.AnchorPath(root)));
        Assert.IsTrue((await Verifier().VerifyAsync(
            root,
            CancellationToken.None)).IsValid);
    }

    [TestMethod]
    public async Task LinkInsideGeneratedRootFailsWithoutFollowingItsTarget()
    {
        using TemporaryDirectory temporary = new();
        var root = Path.Combine(temporary.Path, "Product.Cli.Host");
        await Publisher().PublishCreateAsync(
            root,
            Payloads(),
            CancellationToken.None);
        var outside = Path.Combine(temporary.Path, "outside.txt");
        await File.WriteAllTextAsync(
            outside,
            "outside",
            CancellationToken.None);
        var link = Path.Combine(root, "Generated", "linked.txt");
        try
        {
            File.CreateSymbolicLink(link, outside);
        }
        catch (Exception exception) when (
            exception is UnauthorizedAccessException or
            PlatformNotSupportedException)
        {
            Assert.Inconclusive(
                "The current test environment cannot create a symbolic link.");
            return;
        }

        var result = await Verifier().VerifyAsync(
            root,
            CancellationToken.None);

        Assert.IsTrue(result.Issues.Any(issue =>
            issue.Kind == GeneratedOutputIntegrityIssueKind.Unsafe &&
            issue.Path == "Generated/linked.txt"));
    }

    private static GeneratedOutputPublisher Publisher() =>
        new(new GeneratedOutputSealer(), Verifier());

    private static GeneratedOutputIntegrityVerifier Verifier() =>
        new();

    private static ImmutableArray<GeneratedOutputPayload> Payloads() =>
        [
            new("Program.cs", "program"u8.ToArray()),
            new("Generated/Command.cs", "command"u8.ToArray()),
        ];

    private static void AssertEmbeddedDigest(
        System.Reflection.Assembly assembly,
        string resourceName,
        string expected)
    {
        using var stream = assembly.GetManifestResourceStream(resourceName) ??
            throw new AssertFailedException(
                string.Concat("Missing schema resource ", resourceName));
        var actual = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(
                SHA256.HashData(stream)));
        Assert.AreEqual(expected, actual);
    }

}
