using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Definitions;
using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.TasksCoreDomainConsumerFixture.Contracts;

/// <summary>
/// Proves that consumer-owned immediate, background, and scheduled work can be
/// expressed through Tasks.Core alone.
/// </summary>
public static class DomainTaskCatalog
{
    private static readonly Sha256Digest ExactDigest =
        Sha256Digest.Parse($"sha256:{new string('a', 64)}");

    /// <summary>Gets exact immediate-work meaning.</summary>
    public static TaskDefinition ImmediateDefinition { get; } =
        Definition("immediate");

    /// <summary>Gets exact background-work meaning.</summary>
    public static TaskDefinition BackgroundDefinition { get; } =
        Definition("background");

    /// <summary>Gets exact scheduled-work meaning.</summary>
    public static TaskDefinition ScheduledDefinition { get; } =
        Definition("scheduled");

    /// <summary>Creates one typed immediate-work proposal.</summary>
    public static TaskRequest<ImmediateTaskRequest> ImmediateRequest(string subject) =>
        Request(
            ImmediateDefinition,
            new ImmediateTaskRequest(subject),
            "immediate");

    /// <summary>Creates one typed volatile-background-work proposal.</summary>
    public static TaskRequest<BackgroundTaskRequest> BackgroundRequest(string subject) =>
        Request(
            BackgroundDefinition,
            new BackgroundTaskRequest(subject),
            "background");

    /// <summary>Creates one typed scheduled-work proposal.</summary>
    public static TaskRequest<ScheduledTaskRequest> ScheduledRequest(
        string subject,
        ArtifactReference occurrenceRevision) =>
        Request(
            ScheduledDefinition,
            new ScheduledTaskRequest(subject),
            "scheduled",
            occurrenceRevision);

    /// <summary>Creates versioned trigger intent using a typed descriptor artifact.</summary>
    public static TaskScheduleDefinition Schedule() =>
        new(
            Reference("task-schedule-definition", "scheduled"),
            ScheduledDefinition.Revision,
            Reference("task-activation-binding", "scheduled"),
            Reference("schedule-descriptor", "scheduled-interval"),
            Reference("schema", "scheduled-interval"),
            Reference("profile", "interval-occurrence-calculator"));

    private static TaskDefinition Definition(string name) =>
        new(
            Reference("task-definition", name),
            ProgramKitIdentifier.Parse("pkid:domain:consumer:sample"),
            Reference("contract", $"{name}-request"),
            Reference("contract", $"{name}-response"),
            Reference("contract", $"{name}-failure"),
            Reference("policy", $"{name}-authority"),
            Reference("policy", $"{name}-cancellation"),
            Reference("policy", $"{name}-idempotency"),
            Reference("policy", $"{name}-retry"),
            Reference("policy", $"{name}-observability"),
            Reference("policy", $"{name}-resource"));

    private static TaskRequest<TRequest> Request<TRequest>(
        TaskDefinition definition,
        TRequest payload,
        string name,
        ArtifactReference? occurrenceRevision = null)
        where TRequest : notnull =>
        new(
            Reference("task-request", name),
            definition.Revision,
            definition.RequestContract,
            definition.ResponseContract,
            definition.FailureContract,
            ProgramKitIdentifier.Parse("pkid:actor:consumer:operator"),
            DateTimeOffset.UnixEpoch,
            payload,
            null,
            ImmutableArray<ArtifactReference>.Empty,
            occurrenceRevision);

    private static ArtifactReference Reference(string kind, string name) =>
        new(
            ProgramKitIdentifier.Parse($"pkid:{kind}:consumer:{name}"),
            SemanticVersion.Parse("1.0.0"),
            ExactDigest);
}
