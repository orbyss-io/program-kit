using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Publication;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Sealing;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet;

[TestClass]
public sealed class DotNetVerifyHostCommandOperationTests
{
    [TestMethod]
    public async Task FrozenOperationMapsIntegrityDriftToConformanceFailure()
    {
        var parent = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-verify-host-tests-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(parent);
        try
        {
            var root = Path.Combine(parent, "Product.Cli.Host");
            GeneratedOutputIntegrityVerifier verifier = new();
            GeneratedOutputPublisher publisher = new(
                new GeneratedOutputSealer(),
                verifier);
            await publisher.PublishCreateAsync(
                root,
                [new GeneratedOutputPayload("Program.cs", "program"u8.ToArray())],
                CancellationToken.None);
            DotNetVerifyHostCommandOperation sut = new(verifier);

            var valid = await sut.ExecuteAsync(
                Invocation(root),
                CancellationToken.None);
            Assert.AreEqual(CommandExitCode.Success, valid.ExitCode);

            await File.WriteAllTextAsync(
                Path.Combine(root, "Program.cs"),
                "tampered",
                CancellationToken.None);
            var drift = await sut.ExecuteAsync(
                Invocation(root),
                CancellationToken.None);

            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                drift.ExitCode);
            Assert.AreEqual("PKINT002", drift.Diagnostics.Single().Id);
            Assert.AreEqual("Program.cs", drift.Diagnostics.Single().Path);
            Assert.Contains(
                "Tampered-with Program Kit generated output",
                drift.Diagnostics.Single().Message);
        }
        finally
        {
            if (Directory.Exists(parent))
            {
                Directory.Delete(parent, recursive: true);
            }
        }
    }

    [TestMethod]
    public async Task InvalidRootMapsToFrozenUsageFailure()
    {
        DotNetVerifyHostCommandOperation sut = new(
            new GeneratedOutputIntegrityVerifier());

        var result = await sut.ExecuteAsync(
            Invocation("\0"),
            CancellationToken.None);

        Assert.AreEqual(
            CommandExitCode.UsageOrInputFailure,
            result.ExitCode);
        Assert.AreEqual("PKINT007", result.Diagnostics.Single().Id);
    }

    private static CommandInvocation Invocation(string root)
    {
        var descriptor = CommandDescriptorCatalog.All.Single(
            static candidate =>
                candidate.Key == "dotnet.verify-host");
        return new CommandInvocation(
            descriptor,
            [],
            ImmutableDictionary<string, string>.Empty
                .Add("root", root)
                .Add("diagnostics", "text"));
    }
}
