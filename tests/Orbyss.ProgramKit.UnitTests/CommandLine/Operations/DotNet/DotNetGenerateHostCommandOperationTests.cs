using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet;

[TestClass]
public sealed class DotNetGenerateHostCommandOperationTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    [DataRow("api", "docs/openapi.json")]
    [DataRow("console", "docs/open-console.json")]
    [DataRow("worker", "docs/open-worker.json")]
    public async Task HostGenerationUsesOnlyManifestBoundExactInputs(
        string kindValue,
        string expectedDocumentPath)
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-host-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var serializer = CreateSerializer();
            var profile = DotNetJsonProfiles.ShellBootstrap.Reference;
            var limits = JsonSerializationLimits.Default;
            var inputBytes = "{}"u8.ToArray();
            var inputDigest = Digest(inputBytes);
            var shell = DotNetTestContractFactory.Shell() with
            {
                InputVersionMapRevision = new ArtifactReference(
                    DotNetTestContractFactory.Id("version-map", "inputs"),
                    new SemanticVersion("1.0.0"),
                    inputDigest),
                InputVersionSelectionRevision = new ArtifactReference(
                    DotNetTestContractFactory.Id("version-selection", "inputs"),
                    new SemanticVersion("1.0.0"),
                    inputDigest),
            };
            var shellBytes = serializer.Write(
                shell,
                profile,
                limits).ToArray();
            var shellRevision = new ArtifactReference(
                DotNetTestContractFactory.Id("shell", "reviewed"),
                new SemanticVersion("1.0.0"),
                Digest(shellBytes));
            var kind = kindValue switch
            {
                "api" => DotNetHostKind.Api,
                "console" => DotNetHostKind.Console,
                "worker" => DotNetHostKind.Worker,
                _ => throw new AssertFailedException("Unsupported test host kind."),
            };
            var documentBytes = kind switch
            {
                DotNetHostKind.Api => serializer.Write(
                    DotNetTestContractFactory.ApiDocument(shell) with
                    {
                        Provenance = DotNetTestContractFactory
                            .ApiDocument(shell)
                            .Provenance with
                        {
                            ShellRevision = shellRevision,
                        },
                    },
                    profile,
                    limits).ToArray(),
                DotNetHostKind.Console => serializer.Write(
                    DotNetTestContractFactory.ConsoleDocument(shell) with
                    {
                        Provenance = DotNetTestContractFactory
                            .ConsoleDocument(shell)
                            .Provenance with
                        {
                            ShellRevision = shellRevision,
                        },
                    },
                    profile,
                    limits).ToArray(),
                DotNetHostKind.Worker => serializer.Write(
                    DotNetTestContractFactory.WorkerDocument(shell) with
                    {
                        Provenance = DotNetTestContractFactory
                            .WorkerDocument(shell)
                            .Provenance with
                        {
                            ShellRevision = shellRevision,
                        },
                    },
                    profile,
                    limits).ToArray(),
                _ => throw new AssertFailedException("Unsupported test host kind."),
            };
            var documentRevision = new ArtifactReference(
                DotNetTestContractFactory.Id("document", kindValue),
                new SemanticVersion("1.0.0"),
                Digest(documentBytes));
            var host = shell.Hosts.Single(candidate =>
                candidate.Kind == kind);
            var manifest = new DotNetArtifactInputManifest(
                "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
                new SemanticVersion("1.0.0"),
                [
                    new DotNetArtifactInputEntry(
                        shell.InputVersionMapRevision,
                        "version-map.json"),
                    new DotNetArtifactInputEntry(
                        shell.InputVersionSelectionRevision,
                        "version-selection.json"),
                    new DotNetArtifactInputEntry(
                        documentRevision,
                        string.Concat("open-", kindValue, ".json")),
                ],
                [
                    new DotNetHostDocumentInput(
                        host.Identity,
                        documentRevision),
                ]);
            var manifestBytes = serializer.Write(
                manifest,
                profile,
                limits).ToArray();
            var shellPath = Path.Combine(root, "shell.json");
            var manifestPath = Path.Combine(root, "artifact-manifest.json");
            await File.WriteAllBytesAsync(
                shellPath,
                shellBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                Path.Combine(root, "version-map.json"),
                inputBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                Path.Combine(root, "version-selection.json"),
                inputBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                Path.Combine(root, string.Concat("open-", kindValue, ".json")),
                documentBytes,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                manifestPath,
                manifestBytes,
                TestContext.CancellationToken);
            var output = Path.Combine(root, "generated");
            TestCommandConsole console = new();
            var application = CommandLineComposition.CreateDefault(console);

            var exitCode = await application.RunAsync(
            [
                "dotnet",
                "generate-host",
                kindValue,
                "--shell",
                shellPath,
                "--host",
                host.Identity.Value,
                "--artifact-manifest",
                manifestPath,
                "--output",
                output,
            ],
            TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.Success, exitCode);
            Assert.IsTrue(File.Exists(Path.Combine(output, "GeneratedHost.csproj")));
            Assert.IsTrue(File.Exists(Path.Combine(output, "shell.lock.json")));
            Assert.IsTrue(File.Exists(
                Path.Combine(
                    output,
                    expectedDocumentPath.Replace('/', Path.DirectorySeparatorChar))));
            Assert.IsEmpty(console.StandardError);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder jsonBuilder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(jsonBuilder);
        return new ProgramKitJsonSerializer(
            jsonBuilder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }

    private static Sha256Digest Digest(ReadOnlySpan<byte> content) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(
                System.Security.Cryptography.SHA256.HashData(content))));
}
