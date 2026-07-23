using System.Text;
using Orbyss.ProgramKit.UnitTests.Workbench.Operations.Generation.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Generation;

[TestClass]
public sealed class WorkbenchGenerationServiceTests
{
    private static readonly string[] ExpectedOutputPaths = ["a.txt", "z.txt"];

    [TestMethod]
    public async Task GeneratePublishesOnlyAfterEveryBoundedOutputIsStaged()
    {
        IWorkbenchGenerator<string> generator = new TestWorkbenchGenerator(
        [
            new GeneratedOutput("z.txt", Encoding.UTF8.GetBytes("z")),
            new GeneratedOutput("a.txt", Encoding.UTF8.GetBytes("a")),
        ]);
        var transaction = new TestOutputTransaction();
        IWorkbenchOutputWorkspace workspace = new TestOutputWorkspace(transaction);
        var sut =
            new WorkbenchGenerationService<string>(generator, workspace);

        var result = await sut.GenerateAsync(
            new GenerationRequest<string>(
                "input",
                "declared-root",
                GenerationCollisionPolicy.Fail,
                GenerationLimits.Default),
            CancellationToken.None);

        Assert.IsTrue(result.IsSuccessful);
        Assert.IsTrue(transaction.Committed);
        Assert.IsFalse(transaction.RolledBack);
        Assert.IsNotNull(result.Value);
        Assert.AreSequenceEqual(
            ExpectedOutputPaths,
            result.Value.Outputs.Select(static output => output.RelativePath).ToArray());
    }

    [TestMethod]
    public async Task GenerateRollsBackPrivateStateWhenCancellationPreventsCommit()
    {
        IWorkbenchGenerator<string> generator = new TestWorkbenchGenerator(
        [
            new GeneratedOutput("a.txt", Encoding.UTF8.GetBytes("a")),
        ]);
        var transaction = new TestOutputTransaction();
        IWorkbenchOutputWorkspace workspace = new TestOutputWorkspace(transaction);
        var sut =
            new WorkbenchGenerationService<string>(generator, workspace);
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        var result = await sut.GenerateAsync(
            new GenerationRequest<string>(
                "input",
                "declared-root",
                GenerationCollisionPolicy.Fail,
                GenerationLimits.Default),
            cancellation.Token);

        Assert.IsFalse(result.IsSuccessful);
        Assert.IsFalse(transaction.Committed);
        Assert.IsTrue(transaction.RolledBack);
        Assert.IsEmpty(transaction.Staged);
    }

    [TestMethod]
    public async Task GenerateReportsCommitAndRollbackFailureWithoutAReceipt()
    {
        IWorkbenchGenerator<string> generator = new TestWorkbenchGenerator(
        [
            new GeneratedOutput("a.txt", Encoding.UTF8.GetBytes("a")),
        ]);
        var transaction = new TestOutputTransaction(
            failCommit: true,
            failRollback: true);
        IWorkbenchOutputWorkspace workspace = new TestOutputWorkspace(transaction);
        var sut = new WorkbenchGenerationService<string>(generator, workspace);

        var result = await sut.GenerateAsync(
            new GenerationRequest<string>(
                "input",
                "declared-root",
                GenerationCollisionPolicy.Fail,
                GenerationLimits.Default),
            CancellationToken.None);

        Assert.IsFalse(result.IsSuccessful);
        Assert.IsNull(result.Value);
        Assert.IsFalse(transaction.Committed);
        Assert.IsTrue(result.Validation.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.OutputPublicationFailed));
        Assert.IsTrue(result.Validation.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.OutputRollbackFailed));
    }
}
