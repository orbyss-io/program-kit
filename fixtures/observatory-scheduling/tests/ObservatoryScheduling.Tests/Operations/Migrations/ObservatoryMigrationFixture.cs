using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Migrations;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.Workbench.Operations.Migrations;
using ObservatoryScheduling.Core.Configuration;

namespace ObservatoryScheduling.Tests.Operations.Migrations;

internal static class ObservatoryMigrationFixture
{
    private static readonly ProgramKitIdentifier Owner =
        new("pkid:domain:fixture:observatory-scheduling");

    internal static MigrationAssessmentRequest CreateAssessmentRequest()
    {
        var schema = Revision("schema", "viewing-request");
        var profile = Revision("profile", "observatory-json");
        var contract = Revision("contract", "schedule-viewing");
        var handler = Revision("implementation", "first-available-handler");
        var taskDefinition = Revision("task-definition", "schedule-viewing");
        var schedule = Revision("task-schedule", "nightly-viewing");
        var host = Revision("host", "observatory-worker");
        var generatedHost = Revision("generated", "observatory-worker-source");
        var observed = ImmutableArray.Create(
            schema,
            profile,
            contract,
            handler,
            taskDefinition,
            schedule,
            host,
            generatedHost);
        var nodes = ImmutableArray.Create(
            Node(schema, VersionBoundaryKind.Schema),
            Node(profile, VersionBoundaryKind.SerializationProfile),
            Node(contract, VersionBoundaryKind.Contract),
            Node(handler, VersionBoundaryKind.Implementation),
            Node(taskDefinition, VersionBoundaryKind.TaskDefinition),
            Node(schedule, VersionBoundaryKind.TaskSchedule),
            Node(host, VersionBoundaryKind.HostComposition),
            Node(generatedHost, VersionBoundaryKind.GeneratedArtifact));
        var edges = ImmutableArray.Create(
            Edge("profile-reads-schema", profile, schema, VersionDependencyKind.Reads),
            Edge("contract-reads-schema", contract, schema, VersionDependencyKind.Reads),
            Edge("handler-implements-contract", handler, contract, VersionDependencyKind.Implements),
            Edge("task-uses-contract", taskDefinition, contract, VersionDependencyKind.UsesContract),
            Edge("schedule-selects-task", schedule, taskDefinition, VersionDependencyKind.Schedules),
            Edge("host-composes-handler", host, handler, VersionDependencyKind.Composes),
            Edge("host-selects-profile", host, profile, VersionDependencyKind.SerializesWith),
            Edge("host-selects-schedule", host, schedule, VersionDependencyKind.ConfiguredBy),
            Edge("generated-host-projects-composition", generatedHost, host, VersionDependencyKind.GeneratedBy));
        var mapReference = Reference(
            "version-map",
            "observatory-v1-to-v2",
            "2.0.0");
        var selectionReference = Reference(
            "version-selection",
            "observatory-v1-to-v2",
            "2.0.0");
        var selections = observed
            .Select(static revision => new VersionSelection(
                revision.Identity,
                revision,
                Reference(
                    revision.Identity.Kind,
                    revision.Identity.Name,
                    "2.0.0"),
                Owner))
            .ToImmutableArray();
        var decisions = observed
            .Select(static revision => Decision(
                revision,
                ActionsFor(revision.Identity.Kind)))
            .ToImmutableArray();

        return new MigrationAssessmentRequest(
            mapReference,
            selectionReference,
            new VersionMapDocument(nodes, edges),
            new VersionSelectionDocument(mapReference, selections),
            decisions,
            new MigrationAnalysisLimits(32, 128));
    }

    internal static PendingWorkPolicy CreatePendingWorkPolicy()
    {
        var observed = Revision("task-definition", "schedule-viewing");
        return new PendingWorkPolicy(
            observed,
            Reference(
                observed.Identity.Kind,
                observed.Identity.Name,
                "2.0.0"),
            PendingWorkDisposition.DrainObservedRevision,
            false,
            Evidence("pending-work-drain-policy"));
    }

    private static MigrationBoundaryDecision Decision(
        ArtifactReference revision,
        ImmutableArray<MigrationRequiredAction> actions) =>
        new(
            revision.Identity,
            CompleteCompatibility(),
            MigrationTerminalDisposition.CompatibleAfterActions,
            actions,
            [Evidence(string.Concat("migration-", revision.Identity.Name))],
            string.Concat(
                "The ",
                revision.Identity.Kind,
                " revision is migrated from v1 to v2 only after its ordered actions and evidence complete."));

    private static ImmutableArray<MigrationRequiredAction> ActionsFor(
        string kind) =>
        kind switch
        {
            "schema" =>
            [
                MigrationRequiredAction.MigrateArtifact,
                MigrationRequiredAction.Retest,
            ],
            "profile" =>
            [
                MigrationRequiredAction.Regenerate,
                MigrationRequiredAction.Retest,
            ],
            "contract" or "implementation" =>
            [
                MigrationRequiredAction.Recompile,
                MigrationRequiredAction.Retest,
            ],
            "task-definition" =>
            [
                MigrationRequiredAction.DrainOrMigratePendingWork,
                MigrationRequiredAction.Recompile,
                MigrationRequiredAction.Retest,
            ],
            "task-schedule" =>
            [
                MigrationRequiredAction.DrainOrMigratePendingWork,
                MigrationRequiredAction.RepackageOrRelock,
                MigrationRequiredAction.Retest,
            ],
            "host" or "generated" =>
            [
                MigrationRequiredAction.Regenerate,
                MigrationRequiredAction.Recompile,
                MigrationRequiredAction.RepackageOrRelock,
                MigrationRequiredAction.Retest,
            ],
            _ => [MigrationRequiredAction.Retest],
        };

    private static ImmutableArray<CompatibilityClaim> CompleteCompatibility() =>
        Enum.GetValues<CompatibilityDimension>()
            .Select(static dimension => new CompatibilityClaim(
                dimension,
                CompatibilityClassification.ConditionallyCompatible,
                ["Complete the exact ordered migration actions."]))
            .ToImmutableArray();

    private static VersionRevisionNode Node(
        ArtifactReference revision,
        VersionBoundaryKind kind) =>
        new(revision, kind, Owner, [Evidence(revision.Identity.Name)]);

    private static VersionDependencyEdge Edge(
        string name,
        ArtifactReference source,
        ArtifactReference resolution,
        VersionDependencyKind kind) =>
        new(
            new ProgramKitIdentifier(string.Concat("pkid:edge:fixture:", name)),
            source,
            resolution.Identity,
            kind,
            new SemanticVersionRange("[1.0.0]"),
            resolution,
            DependencyExposure.Private,
            [
                CompatibilityDimension.SemanticBehavior,
                CompatibilityDimension.GeneratedArtifacts,
            ],
            [Evidence(string.Concat("edge-", name))]);

    private static ArtifactReference Revision(string kind, string name) =>
        Reference(kind, name, "1.0.0");

    private static ArtifactReference Evidence(string name) =>
        Reference("evidence", name, "1.0.0");

    private static ArtifactReference Reference(
        string kind,
        string name,
        string version) =>
        ObservatoryRevisions.Reference(
            string.Concat("pkid:", kind, ":fixture:", name),
            version);
}
