using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Contracts.Time;
using ObservatoryScheduling.Core.Tasks;

namespace ObservatoryScheduling.Core.Configuration;

/// <summary>Creates the fixture-owned, explicitly selectable JSON contributions.</summary>
public static class ObservatoryJsonContributionCatalog
{
    /// <summary>Creates the typed observatory-window converter contribution.</summary>
    public static IJsonSerializationContribution CreateWindowConverter() =>
        new TypedJsonConverterContribution<ObservatoryWindow>(
            Descriptor(
                "pkid:json-contribution:fixture:observatory-window",
                JsonSerializationContributionKind.TypedConverter,
                [
                    "ObservatoryScheduling.Core.Contracts.Time.ObservatoryWindow, ObservatoryScheduling.Core",
                ]),
            new ObservatoryWindowJsonConverter());

    /// <summary>Creates the source-generated fixture model contribution.</summary>
    public static IJsonSerializationContribution CreateModelContext() =>
        new JsonTypeInfoResolverContribution(
            Descriptor(
                "pkid:json-contribution:fixture:observatory-models",
                JsonSerializationContributionKind.TypeInfoResolver,
                [
                    "ObservatoryScheduling.Core.Contracts.Scheduling.ViewingRequest, ObservatoryScheduling.Core",
                    "ObservatoryScheduling.Core.Contracts.Scheduling.ViewingSession, ObservatoryScheduling.Core",
                    "ObservatoryScheduling.Core.Tasks.ScheduleViewingTaskRequest, ObservatoryScheduling.Core",
                    "ObservatoryScheduling.Core.Tasks.ScheduleViewingTaskResponse, ObservatoryScheduling.Core",
                ]),
            ObservatoryJsonContext.Default);

    private static JsonSerializationContributionDescriptor Descriptor(
        string identity,
        JsonSerializationContributionKind kind,
        ImmutableArray<string> targets)
    {
        var revision = ObservatoryRevisions.Reference(identity);
        return new JsonSerializationContributionDescriptor(
            new JsonSerializationContributionRef(
                revision.Identity,
                revision.Version,
                revision.Digest),
            new ProgramKitIdentifier("pkid:package:fixture:observatory-core"),
            ObservatoryJsonProfile.Identity,
            ObservatoryJsonProfile.Range,
            kind,
            targets,
            [],
            []);
    }
}
