using System.Collections.Immutable;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Validation;

[TestClass]
public sealed class DotNetIntegratorDocumentValidatorTests
{
    [TestMethod]
    public void TypedApiConsoleAndWorkerDocumentsPass()
    {
        var shell = DotNetTestContractFactory.Shell();
        DotNetIntegratorDocumentValidator sut = new();

        var api = sut.Validate(DotNetTestContractFactory.ApiDocument(shell));
        var console = sut.Validate(DotNetTestContractFactory.ConsoleDocument(shell));
        var worker = sut.Validate(DotNetTestContractFactory.WorkerDocument(shell));

        Assert.IsTrue(api.IsValid);
        Assert.IsTrue(console.IsValid);
        Assert.IsTrue(worker.IsValid);
    }

    [TestMethod]
    public void ConsoleOptionAliasCollisionFailsClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        var command = document.Commands[0];
        var duplicate = command.Options[0] with
        {
            LongName = "other",
            Aliases = ["--number"],
        };
        document = document with
        {
            Commands = [command with { Options = command.Options.Add(duplicate) }],
        };
        DotNetIntegratorDocumentValidator sut = new();

        var result = sut.Validate(document);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Id == DotNetDiagnosticIds.InvalidIntegratorDocument));
    }

    [TestMethod]
    public void ConsoleCommandAliasCollisionFailsClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        var command = document.Commands[0];
        document = document with
        {
            Commands =
            [
                command,
                command with
                {
                    OperationRevision = DotNetTestContractFactory.Ref(
                        "operation",
                        "second",
                        '8'),
                    Path = ["second"],
                    Aliases = [["execute"]],
                },
            ],
            Provenance = document.Provenance with
            {
                OperationRevisions =
                [
                    command.OperationRevision,
                    DotNetTestContractFactory.Ref("operation", "second", '8'),
                ],
            },
        };
        DotNetIntegratorDocumentValidator sut = new();

        var result = sut.Validate(document);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static item =>
            item.Id == DotNetDiagnosticIds.InvalidIntegratorDocument));
    }

    [TestMethod]
    public void ConsumerOwnedResultUnionAndRelatedOperationRemainOpaqueReferences()
    {
        var shell = DotNetTestContractFactory.Shell();
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        var command = document.Commands[0];
        var unionSchema = DotNetTestContractFactory.Ref(
            "schema",
            "terminal-result-or-continuation",
            '8');
        command = command with
        {
            StandardOutput = new OpenConsoleStreamContract(
                "stdout",
                "application/json",
                unionSchema,
                true),
        };
        document = document with { Commands = [command] };
        DotNetIntegratorDocumentValidator sut = new();

        var result = sut.Validate(document);

        Assert.IsTrue(result.IsValid);
        Assert.DoesNotContain(
            static type =>
                type.Name.Contains("Continuation", StringComparison.Ordinal) ||
                type.Name.Contains("Semantic", StringComparison.Ordinal),
            typeof(DotNetIntegratorDocumentValidator).Assembly.GetExportedTypes());
    }
}
