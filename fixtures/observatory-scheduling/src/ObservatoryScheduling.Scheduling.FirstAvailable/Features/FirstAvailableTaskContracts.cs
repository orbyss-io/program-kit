using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Bindings;
using Orbyss.ProgramKit.Tasks.Core.Definitions;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Policies;
using Orbyss.ProgramKit.Tasks.Registration;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Evidence;
using ObservatoryScheduling.Core.Configuration;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Exact task, handler, schedule, and policy selections owned by the feature.</summary>
public static class FirstAvailableTaskContracts
{
    /// <summary>Gets the selected task definition.</summary>
    public static TaskDefinition Definition { get; } = new(
        ObservatoryRevisions.Reference(
            "pkid:task-definition:fixture:schedule-viewing"),
        new ProgramKitIdentifier(
            "pkid:package:fixture:observatory-scheduling-first-available"),
        ObservatoryRevisions.Reference(
            "pkid:contract:fixture:schedule-viewing-request"),
        ObservatoryRevisions.Reference(
            "pkid:contract:fixture:schedule-viewing-response"),
        ObservatoryRevisions.Reference(
            "pkid:contract:fixture:schedule-viewing-failure"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:observatory-authority"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:observatory-cancellation"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:observatory-idempotency"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:observatory-retry"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:observatory-observability"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:observatory-resource"));

    /// <summary>Gets the exact feature revision selected by task activation.</summary>
    public static ArtifactReference FeatureRevision { get; } =
        ObservatoryRevisions.Reference(
            "pkid:feature:fixture:first-available");

    /// <summary>Gets the selected handler revision.</summary>
    public static ArtifactReference HandlerRevision { get; } =
        ObservatoryRevisions.Reference(
            "pkid:handler:fixture:schedule-viewing");

    /// <summary>Gets the selected in-process runtime revision.</summary>
    public static ArtifactReference RuntimeRevision { get; } =
        ObservatoryRevisions.Reference(
            "pkid:runtime:program-kit:tasks-in-process");

    /// <summary>Gets the task dispatch middleware revision.</summary>
    public static ArtifactReference MiddlewareRevision { get; } =
        ObservatoryRevisions.Reference(
            "pkid:middleware:fixture:schedule-viewing-dispatch");

    /// <summary>Gets the selected activation binding.</summary>
    public static TaskActivationBinding Binding { get; } = new(
        ObservatoryRevisions.Reference(
            "pkid:task-binding:fixture:schedule-viewing"),
        Definition.Revision,
        HandlerRevision,
        FeatureRevision,
        new ProgramKitIdentifier(
            "pkid:activation:fixture:first-available"),
        RuntimeRevision,
        [MiddlewareRevision],
        Definition.RetryPolicy,
        Definition.IdempotencyPolicy,
        ObservatoryRevisions.Reference(
            "pkid:task-schedule:fixture:nightly-viewing"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:nightly-misfire"),
        ObservatoryRevisions.Reference(
            "pkid:policy:fixture:nightly-overlap"));

    /// <summary>Gets the selected Cronos occurrence-calculator profile.</summary>
    public static ArtifactReference CronosProfile { get; } =
        ObservatoryRevisions.Reference(
            "pkid:schedule-profile:program-kit:cronos-0-13");

    /// <summary>Gets the nightly schedule definition.</summary>
    public static TaskScheduleDefinition Schedule { get; } = new(
        Binding.ScheduleRevision!,
        Definition.Revision,
        Binding.Revision,
        ObservatoryRevisions.Reference(
            "pkid:schedule-descriptor:fixture:nightly-viewing"),
        ObservatoryRevisions.Reference(
            "pkid:schema:program-kit:cronos-schedule-descriptor"),
        CronosProfile);

    /// <summary>Gets the fixed, bounded UTC Cronos descriptor.</summary>
    public static CronosScheduleDescriptor ScheduleDescriptor { get; } = new(
        "0 20 * * *",
        CronosScheduleFormat.Standard,
        null,
        "UTC",
        CronosProfile,
        new CronosTimeZoneSelectionEvidence(
            "fixture-utc",
            "1",
            new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero),
            new DateTimeOffset(2030, 1, 1, 0, 0, 0, TimeSpan.Zero),
            new Sha256Digest(
                "sha256:28ec1a773ac30eb9f339b5e1039f5dea067d59f80c625dc41a3763c69fab4627")));

    /// <summary>Gets the bounded missed-occurrence policy.</summary>
    public static TaskMisfirePolicyRegistration MisfirePolicy { get; } = new(
        Binding.MisfirePolicyRevision!,
        TaskMisfirePolicyKind.FireOnceNow,
        1);

    /// <summary>Gets the volatile no-overlap policy.</summary>
    public static TaskOverlapPolicyRegistration OverlapPolicy { get; } = new(
        Binding.OverlapPolicyRevision!,
        TaskOverlapPolicyKind.Skip);
}
