using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.UnitTests.Tasks.Composition.TestSupport;

internal static class TaskRegistrationTestValues
{
    internal static ITaskHandlerRegistration Handler(
        string range = "[1.0.0]") =>
        new TaskHandlerRegistration<
            TestTaskRequestModel,
            TestTaskResponseModel,
            TestTaskHandler>(
            TasksCoreTestValues.Binding().HandlerRevision,
            new SemanticVersionRange(range));

    internal static TaskRegistrationSet Complete(
        ImmutableArray<TaskActivationBindingRegistration>? bindings = null,
        ImmutableArray<ITaskHandlerRegistration>? handlers = null) =>
        new(
            [new TaskDefinitionRegistration(TasksCoreTestValues.Definition())],
            handlers ?? [Handler()],
            bindings ??
                [
                    new TaskActivationBindingRegistration(
                        TasksCoreTestValues.Binding()),
                ],
            [
                new TaskFeatureRegistration(
                    TasksCoreTestValues.Binding().OwningFeatureRevision),
            ],
            [],
            [],
            [],
            [],
            [],
            []);
}
