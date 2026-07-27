using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Scheduling;
using Orbyss.ProgramKit.UnitTests.Tasks.Composition.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Scheduling.TestSupport;

internal sealed class TestTaskOccurrenceRequestFactory :
    ITaskOccurrenceRequestFactory<TestTaskRequestModel>
{
    public ValueTask<TaskRequest<TestTaskRequestModel>> CreateAsync(
        TaskOccurrence occurrence,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var definition = TasksCoreTestValues.Definition();
        return ValueTask.FromResult(
            new TaskRequest<TestTaskRequestModel>(
                TestContractValues.Reference(
                    string.Concat(
                        "pkid:task-request:program-kit:scheduled-",
                        occurrence.Sequence.ToString(
                            System.Globalization.CultureInfo.InvariantCulture))),
                occurrence.DefinitionRevision,
                definition.RequestContract,
                definition.ResponseContract,
                definition.FailureContract,
                TasksCoreTestValues.Request().RequestedBy,
                occurrence.EvaluatedAt,
                new TestTaskRequestModel("scheduled"),
                occurrence.Revision.Identity.Value,
                [occurrence.Revision],
                occurrence.Revision));
    }
}
