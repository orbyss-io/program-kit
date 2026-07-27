using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Tasks.Composition;
using Orbyss.ProgramKit.Tasks.Core.Validation;
using Orbyss.ProgramKit.Tasks.Diagnostics;
using Orbyss.ProgramKit.Tasks.Registration;
using Orbyss.ProgramKit.UnitTests.Tasks.Composition.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Tasks.Composition;

[TestClass]
public sealed class TaskRegistryFactoryTests
{
    [TestMethod]
    public void IdenticalRegistrationsCollapseBeforeFreeze()
    {
        TaskRegistryFactory sut = Factory();
        var handler = TaskRegistrationTestValues.Handler();
        var registrations = TaskRegistrationTestValues.Complete(
            handlers: [handler, handler]);

        var registry = sut.Create(registrations);

        Assert.ContainsSingle(registry.Handlers);
    }

    [TestMethod]
    public void ConflictingStableHandlerRegistrationFailsClosed()
    {
        TaskRegistryFactory sut = Factory();
        var registrations = TaskRegistrationTestValues.Complete(
            handlers:
            [
                TaskRegistrationTestValues.Handler(),
                TaskRegistrationTestValues.Handler("[1.0.0,2.0.0)"),
            ]);

        var exception = Assert.ThrowsExactly<TaskCompositionException>(
            () => sut.Create(registrations));

        Assert.IsTrue(
            exception.Validation.Diagnostics.Any(
                diagnostic => diagnostic.Id == "PKTAS002"));
    }

    [TestMethod]
    public void MultipleBindingsForOneDefinitionFailComposition()
    {
        TaskRegistryFactory sut = Factory();
        var second = TasksCoreTestValues.Binding() with
        {
            Revision = TestContractValues.Reference(
                "pkid:task-activation-binding:program-kit:second-binding"),
        };
        var registrations = TaskRegistrationTestValues.Complete(
            bindings:
            [
                new TaskActivationBindingRegistration(
                    TasksCoreTestValues.Binding()),
                new TaskActivationBindingRegistration(second),
            ]);

        var exception = Assert.ThrowsExactly<TaskCompositionException>(
            () => sut.Create(registrations));

        Assert.IsTrue(
            exception.Validation.Diagnostics.Any(
                diagnostic => diagnostic.Id == "PKTAS002"));
    }

    [TestMethod]
    public void BindingWithMissingExactMiddlewareFailsComposition()
    {
        TaskRegistryFactory sut = Factory();
        var binding = TasksCoreTestValues.Binding() with
        {
            MiddlewareRevisions =
            [
                TestContractValues.Reference(
                    "pkid:middleware:program-kit:missing"),
            ],
        };
        var registrations = TaskRegistrationTestValues.Complete(
            bindings: [new TaskActivationBindingRegistration(binding)]);

        var exception = Assert.ThrowsExactly<TaskCompositionException>(
            () => sut.Create(registrations));

        Assert.IsTrue(
            exception.Validation.Diagnostics.Any(
                diagnostic => diagnostic.Id == "PKTAS003"));
    }

    [TestMethod]
    public void RegistrationAfterFreezeIsRejected()
    {
        IServiceCollection services = new ServiceCollection();
        var catalog = services.AddProgramKitTasks();
        catalog.Import(TaskRegistrationTestValues.Complete());
        using var provider = services.BuildServiceProvider();
        var coordinator =
            provider.GetRequiredService<ITaskRegistryCoordinator>();
        coordinator.Freeze();

        var exception = Assert.ThrowsExactly<TaskCompositionException>(
            () => catalog.Add(
                new TaskDefinitionRegistration(
                    TasksCoreTestValues.Definition())));

        Assert.IsTrue(
            exception.Validation.Diagnostics.Any(
                diagnostic => diagnostic.Id == "PKTAS007"));
    }

    private static TaskRegistryFactory Factory() =>
        new TaskRegistryFactory(
            new TaskContractValidator(
                new ArtifactReferenceValidator()),
            new ArtifactReferenceValidator());
}
