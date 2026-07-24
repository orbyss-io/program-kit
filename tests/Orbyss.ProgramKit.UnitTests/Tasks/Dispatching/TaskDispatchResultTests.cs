namespace Orbyss.ProgramKit.UnitTests.Tasks.Dispatching;

[TestClass]
public sealed class TaskDispatchResultTests
{
    [TestMethod]
    public void RejectionOccursBeforeAnInstanceExists()
    {
        ITaskContractValidator validator = TasksCoreTestValues.Validator();
        var result = new TaskDispatchResult(
            TasksCoreTestValues.Request().Revision,
            TaskDispatchDisposition.Rejected,
            null,
            []);

        Assert.AreEqual(TaskDispatchDisposition.Rejected, result.Disposition);
        Assert.IsNull(result.InstanceRevision);
        Assert.IsTrue(validator.Validate(result).IsValid);
    }

    [TestMethod]
    public void RejectedDispatchWithAnInstanceFailsClosed()
    {
        ITaskContractValidator sut = TasksCoreTestValues.Validator();
        var contradictory = new TaskDispatchResult(
            TasksCoreTestValues.Request().Revision,
            TaskDispatchDisposition.Rejected,
            TasksCoreTestValues.Instance().Revision,
            []);

        var result = sut.Validate(contradictory);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == TasksCoreDiagnosticIds.InvalidTaskLifecycleView &&
            diagnostic.Path == "/disposition"));
    }
}
