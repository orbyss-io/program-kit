using System.Text;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Refresh;

[TestClass]
public sealed class DotNetHostRefreshServiceTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task PreviewCreateIsDeterministicAndDoesNotMutate()
    {
        var root = CreateRoot();
        try
        {
            var request = await WriteRequestAsync(
                root,
                includeBuild: false,
                TestContext.CancellationToken);
            RefreshTestHostGenerationService generation = new();
            DotNetHostRefreshService sut = Service(
                generation,
                new RefreshTestCompilerHarness());

            var first = await sut.RefreshAsync(
                request,
                preview: true,
                buildConsumer: false,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);
            var second = await sut.RefreshAsync(
                request,
                preview: true,
                buildConsumer: false,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);

            Assert.AreEqual(first, second);
            Assert.AreEqual("create", first.Action);
            Assert.IsFalse(Directory.Exists(Path.Combine(root, "host")));
        }
        finally
        {
            DeleteRoot(root);
        }
    }

    [TestMethod]
    public async Task RefreshCreatesLeavesIdenticalBytesAndReplacesValidChange()
    {
        var root = CreateRoot();
        try
        {
            var request = await WriteRequestAsync(
                root,
                includeBuild: false,
                TestContext.CancellationToken);
            RefreshTestHostGenerationService generation = new();
            DotNetHostRefreshService sut = Service(
                generation,
                new RefreshTestCompilerHarness());

            var created = await sut.RefreshAsync(
                request,
                preview: false,
                buildConsumer: false,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);
            var hostFile = Path.Combine(
                root,
                "host",
                "ProgramKitGenerated",
                "Program.cs");
            var createdWrite = File.GetLastWriteTimeUtc(hostFile);
            var unchanged = await sut.RefreshAsync(
                request,
                preview: false,
                buildConsumer: false,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);
            Assert.AreEqual(createdWrite, File.GetLastWriteTimeUtc(hostFile));
            generation.Content = "second\n";
            var replaced = await sut.RefreshAsync(
                request,
                preview: false,
                buildConsumer: false,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);

            Assert.AreEqual("create", created.Action);
            Assert.AreEqual("unchanged", unchanged.Action);
            Assert.AreEqual("replace", replaced.Action);
            Assert.AreEqual(
                "second\n",
                await File.ReadAllTextAsync(
                    hostFile,
                    TestContext.CancellationToken));
        }
        finally
        {
            DeleteRoot(root);
        }
    }

    [TestMethod]
    public async Task DriftRefusesUntilRepairAndRepairQuarantinesBytes()
    {
        var root = CreateRoot();
        try
        {
            var request = await WriteRequestAsync(
                root,
                includeBuild: false,
                TestContext.CancellationToken);
            RefreshTestHostGenerationService generation = new();
            DotNetHostRefreshService sut = Service(
                generation,
                new RefreshTestCompilerHarness());
            _ = await sut.RefreshAsync(
                request,
                preview: false,
                buildConsumer: false,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);
            var hostFile = Path.Combine(
                root,
                "host",
                "ProgramKitGenerated",
                "Program.cs");
            await File.WriteAllTextAsync(
                hostFile,
                "tampered\n",
                TestContext.CancellationToken);

            var exception = await Assert.ThrowsExactlyAsync<
                DotNetHostRefreshException>(
                () => sut.RefreshAsync(
                    request,
                    preview: false,
                    buildConsumer: false,
                    repairGeneratedOutput: false,
                    TestContext.CancellationToken).AsTask());
            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                exception.ExitCode);
            Assert.AreEqual(
                "tampered\n",
                await File.ReadAllTextAsync(
                    hostFile,
                    TestContext.CancellationToken));

            generation.Content = "repaired\n";
            var repaired = await sut.RefreshAsync(
                request,
                preview: false,
                buildConsumer: false,
                repairGeneratedOutput: true,
                TestContext.CancellationToken);

            Assert.AreEqual("repair", repaired.Action);
            Assert.IsNotNull(repaired.QuarantineDigest);
            var quarantined = Path.Combine(
                root,
                ".program-kit-quarantine",
                "host",
                repaired.QuarantineDigest["sha256:".Length..],
                "root",
                "ProgramKitGenerated",
                "Program.cs");
            Assert.AreEqual(
                "tampered\n",
                await File.ReadAllTextAsync(
                    quarantined,
                    TestContext.CancellationToken));
            Assert.AreEqual(
                "repaired\n",
                await File.ReadAllTextAsync(
                    hostFile,
                    TestContext.CancellationToken));
        }
        finally
        {
            DeleteRoot(root);
        }
    }

    [TestMethod]
    public async Task ConsumerBuildRunsOnlyWithFlagAndExactRequestInputs()
    {
        var root = CreateRoot();
        try
        {
            var request = await WriteRequestAsync(
                root,
                includeBuild: true,
                TestContext.CancellationToken);
            RefreshTestCompilerHarness harness = new();
            DotNetHostRefreshService sut = Service(
                new RefreshTestHostGenerationService(),
                harness);

            _ = await sut.RefreshAsync(
                request,
                preview: true,
                buildConsumer: false,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);
            Assert.AreEqual(0, harness.CallCount);

            _ = await sut.RefreshAsync(
                request,
                preview: true,
                buildConsumer: true,
                repairGeneratedOutput: false,
                TestContext.CancellationToken);
            Assert.AreEqual(1, harness.CallCount);
        }
        finally
        {
            DeleteRoot(root);
        }
    }

    private static DotNetHostRefreshService Service(
        RefreshTestHostGenerationService generation,
        RefreshTestCompilerHarness harness) =>
        new(
            generation,
            new GeneratedOutputIntegrityVerifier(),
            harness,
            new DotNetHostRefreshSerializer());

    private static async Task<string> WriteRequestAsync(
        string root,
        bool includeBuild,
        CancellationToken cancellationToken)
    {
        var request = Path.Combine(root, "generation-request.json");
        var consumerBuild = includeBuild
            ?
            """
            {
              "workingDirectory": "consumer",
              "projectPath": "consumer/Consumer.csproj",
              "evidenceOutputPath": "consumer/evidence.json",
              "participationReceiptPaths": [],
              "exceptionUseReceiptPaths": [],
              "packagePaths": [],
              "maximumCapturedOutputBytes": 4096,
              "performanceBudgetMilliseconds": 60000
            }
            """
            : "null";
        var json = string.Concat(
            """
            {
              "schemaVersion": "1.0.0",
              "programKitVersion": "0.1.0-alpha.3",
              "kind": "console",
              "shellPath": "shell.json",
              "hostIdentity": "pkid:host:test:cli",
              "artifactManifestPath": "manifest.json",
              "outputRoot": "host",
              "consumerBuild":
            """,
            consumerBuild,
            "\n}\n");
        await File.WriteAllTextAsync(
            request,
            json,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
            cancellationToken);
        return request;
    }

    private static string CreateRoot()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-refresh-tests-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        return root;
    }

    private static void DeleteRoot(string root)
    {
        if (Directory.Exists(root))
        {
            Directory.Delete(root, recursive: true);
        }
    }
}
