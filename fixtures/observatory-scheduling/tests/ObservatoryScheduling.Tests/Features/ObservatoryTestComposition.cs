using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Modularity.Composition;
using Orbyss.ProgramKit.Modularity.Contributions;
using Orbyss.ProgramKit.Modularity.InProcess.Contributions;
using Orbyss.ProgramKit.Modularity.InProcess.Middleware;
using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Modularity.Ordering;
using ObservatoryScheduling.Core.Configuration;
using ObservatoryScheduling.Core.Contracts.Contributions;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Scheduling.FirstAvailable.Features;

namespace ObservatoryScheduling.Tests.Features;

internal static class ObservatoryTestComposition
{
    internal static IProgramKitMiddlewarePipeline<ViewingRequest, ViewingSession?>
        CreatePipeline()
    {
        var descriptor = new ModularityRegistrationDescriptor(
            ObservatoryRevisions.Reference(
                "pkid:middleware:fixture:first-available-selection"),
            new ProgramKitIdentifier(
                "pkid:package:fixture:observatory-scheduling-first-available"),
            ModularityOrderDescriptor.Default);
        var factory = new MiddlewareRegistryFactory(
            new ArtifactReferenceValidator());
        var registry = factory.Create(
            [
                new MiddlewareRegistration<ViewingRequest, ViewingSession?>(
                    descriptor,
                    new FirstAvailableSelectionMiddleware()),
            ]);
        return new InProcessMiddlewarePipeline<ViewingRequest, ViewingSession?>(
            registry);
    }

    internal static IDomainContributionPublisher CreatePublisher(
        ViewingScheduledRecorder recorder)
    {
        ArgumentNullException.ThrowIfNull(recorder);
        var descriptor = new ModularityRegistrationDescriptor(
            ObservatoryRevisions.Reference(
                "pkid:handler:fixture:record-viewing-scheduled"),
            new ProgramKitIdentifier(
                "pkid:package:fixture:observatory-tests"),
            ModularityOrderDescriptor.Default);
        var factory = new DomainContributionRegistryFactory(
            new ArtifactReferenceValidator());
        var registry = factory.Create(
            [
                new TypedDomainContributionHandlerRegistration<ViewingScheduled>(
                    descriptor,
                    recorder),
            ]);
        return new InProcessDomainContributionPublisher(registry);
    }
}
