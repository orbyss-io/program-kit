using System.Text;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Execution;

[TestClass]
public sealed class CommandApplicationTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task DeferredBackendFailsClosedWithCanonicalJsonDiagnostic()
    {
        TestCommandConsole console = new();
        var sut = CommandLineComposition.CreateDefault(console);

        var exitCode = await sut.RunAsync(
        [
            "capabilities",
            "verify-bundle",
            "bundle.json",
            "--diagnostics",
            "json",
        ],
        TestContext.CancellationToken);

        Assert.AreEqual(CommandExitCode.UsageOrInputFailure, exitCode);
        Assert.IsEmpty(console.StandardOutput);
        Assert.AreEqual(
            "{\"diagnostics\":[{\"id\":\"PKCLI004\",\"message\":\"The operation backend is owned by PK-W070 and is not registered.\",\"path\":\"/command\",\"severity\":\"error\"}],\"exitCode\":2}",
            Encoding.UTF8.GetString(console.StandardError));
    }

    [TestMethod]
    public async Task NormalizeWritesCanonicalBytesToStandardOutput()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var input = Path.Combine(root, "input.json");
            await File.WriteAllBytesAsync(
                input,
                Encoding.UTF8.GetBytes("{\"z\":2,\"a\":1}"),
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var sut = CommandLineComposition.CreateDefault(console);

            var exitCode = await sut.RunAsync(
            [
                "normalize",
                input,
                "--output",
                "-",
            ],
            TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.Success, exitCode);
            Assert.AreEqual(
                "{\"a\":1,\"z\":2}",
                Encoding.UTF8.GetString(console.StandardOutput));
            Assert.IsEmpty(console.StandardError);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task DigestIsStableAcrossPropertyOrder()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var first = Path.Combine(root, "first.json");
            var second = Path.Combine(root, "second.json");
            await File.WriteAllBytesAsync(
                first,
                Encoding.UTF8.GetBytes("{\"z\":2,\"a\":1}"),
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                second,
                Encoding.UTF8.GetBytes("{\"a\":1,\"z\":2}"),
                TestContext.CancellationToken);
            TestCommandConsole firstConsole = new();
            TestCommandConsole secondConsole = new();
            var firstApplication = CommandLineComposition.CreateDefault(firstConsole);
            var secondApplication = CommandLineComposition.CreateDefault(secondConsole);

            var firstExit = await firstApplication.RunAsync(
                ["digest", first],
                TestContext.CancellationToken);
            var secondExit = await secondApplication.RunAsync(
                ["digest", second],
                TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.Success, firstExit);
            Assert.AreEqual(CommandExitCode.Success, secondExit);
            Assert.AreSequenceEqual(
                firstConsole.StandardOutput,
                secondConsole.StandardOutput);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task ValidateMapsSchemaFailureToConformanceExit()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var input = Path.Combine(root, "invalid-manifest.json");
            await File.WriteAllBytesAsync(
                input,
                Encoding.UTF8.GetBytes(
                    "{\"$schema\":\"pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0\",\"version\":\"1.0.0\"}"),
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var sut = CommandLineComposition.CreateDefault(console);

            var exitCode = await sut.RunAsync(
                ["validate", input],
                TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.ConformanceFailure, exitCode);
            Assert.IsEmpty(console.StandardOutput);
            Assert.Contains("PKWB002", Encoding.UTF8.GetString(console.StandardError));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task InvalidJsonMapsToInputExitInsteadOfInternalFailure()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var input = Path.Combine(root, "invalid.json");
            await File.WriteAllBytesAsync(
                input,
                "{"u8.ToArray(),
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var sut = CommandLineComposition.CreateDefault(console);

            var exitCode = await sut.RunAsync(
                ["digest", input],
                TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.UsageOrInputFailure, exitCode);
            Assert.Contains(
                "PKCLI002",
                Encoding.UTF8.GetString(console.StandardError));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }
}
