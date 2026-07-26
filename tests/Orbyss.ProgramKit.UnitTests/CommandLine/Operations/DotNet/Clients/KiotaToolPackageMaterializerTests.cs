using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;
using Orbyss.ProgramKit.CommandLine.Operations.Files;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Clients;

[TestClass]
public sealed class KiotaToolPackageMaterializerTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task UnreviewedPackageBytesFailBeforeExtraction()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-kiota-package-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var package = Path.Combine(root, "kiota.nupkg");
            await File.WriteAllBytesAsync(
                package,
                [0x50, 0x4b, 0x03, 0x04],
                TestContext.CancellationToken);
            KiotaToolPackageMaterializer materializer =
                new(new CommandFileSystem());
            var output = Path.Combine(root, "tool");

            var exception = await Assert.ThrowsAsync<KiotaGenerationException>(
                async () => await materializer.MaterializeAsync(
                    package,
                    output,
                    TestContext.CancellationToken));

            Assert.AreEqual(
                KiotaGenerationDiagnosticIds.InvalidToolPackage,
                exception.DiagnosticId);
            Assert.AreEqual(
                CommandExitCode.UsageOrInputFailure,
                exception.ExitCode);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }
}
