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

    internal static MigrationAssessmentRequest
        CreatePackagePublishAssessmentRequest()
    {
        var baseline = CreateAssessmentRequest();
        var contract = Revision("contract", "schedule-viewing");
        var handler = Revision("implementation", "first-available-handler");
        var taskDefinition = Revision("task-definition", "schedule-viewing");
        var generatedHost = Revision(
            "generated",
            "observatory-worker-source");
        var packages = ImmutableArray.Create(
            (
                Revision: PackageRevision(
                    "Orbyss.ProgramKit.Tasks.Core",
                    "0.1.0-alpha.2",
                    "program-kit"),
                Target: taskDefinition),
            (
                Revision: PackageRevision(
                    "Orbyss.ProgramKit.DotNet",
                    "0.1.0-alpha.2",
                    "program-kit"),
                Target: generatedHost),
            (
                Revision: PackageRevision(
                    "Orbyss.ProgramKit.CommandLine",
                    "0.1.0-alpha.2",
                    "program-kit"),
                Target: generatedHost),
            (
                Revision: PackageRevision(
                    "ObservatoryScheduling.Constraints.DarknessWindow",
                    "0.1.0-fixture.1",
                    "fixture"),
                Target: contract),
            (
                Revision: PackageRevision(
                    "ObservatoryScheduling.Scheduling.FirstAvailable",
                    "0.1.0-fixture.1",
                    "fixture"),
                Target: handler),
            (
                Revision: PackageRevision(
                    "ObservatoryScheduling.Visibility.Static",
                    "0.1.0-fixture.1",
                    "fixture"),
                Target: contract));
        var consumers = ImmutableArray.Create(
            (
                Revision: Reference(
                    "consumer",
                    "contracts-only",
                    "1.0.0"),
                Package: packages[0].Revision),
            (
                Revision: Reference(
                    "consumer",
                    "dotnet-contracts",
                    "1.0.0"),
                Package: packages[1].Revision),
            (
                Revision: Reference(
                    "consumer",
                    "command-line",
                    "1.0.0"),
                Package: packages[2].Revision),
            (
                Revision: Reference(
                    "consumer",
                    "schema-discovery",
                    "1.0.0"),
                Package: packages[0].Revision),
            (
                Revision: Reference(
                    "consumer",
                    "observatory-composition",
                    "1.0.0"),
                Package: packages[4].Revision));
        var hostKinds = ImmutableArray.Create("api", "console", "worker");
        var profiles = hostKinds.Select(kind =>
                Reference(
                    "publish-profile",
                    string.Concat("observatory-", kind),
                    "1.0.0"))
            .ToImmutableArray();
        var leaves = hostKinds.Select(kind =>
                Reference(
                    "publish-leaf",
                    string.Concat("observatory-", kind),
                    "2.0.0"))
            .ToImmutableArray();
        var manifests = hostKinds.Select(kind =>
                Reference(
                    "local-publish-manifest",
                    string.Concat("observatory-", kind),
                    "1.0.0"))
            .ToImmutableArray();
        var additionalNodes = packages
            .Select(package => Node(
                package.Revision,
                VersionBoundaryKind.Package))
            .Concat(consumers.Select(consumer => Node(
                consumer.Revision,
                VersionBoundaryKind.ExternalConsumer)))
            .Concat(profiles.Select(profile => Node(
                profile,
                VersionBoundaryKind.Configuration)))
            .Concat(leaves.Select(leaf => Node(
                leaf,
                VersionBoundaryKind.GeneratedArtifact)))
            .Concat(manifests.Select(manifest => Node(
                manifest,
                VersionBoundaryKind.Artifact)))
            .ToImmutableArray();
        var additionalEdges = ImmutableArray.CreateBuilder<
            VersionDependencyEdge>();
        foreach (var package in packages)
        {
            additionalEdges.Add(ExactEdge(
                string.Concat(
                    "package-",
                    package.Revision.Identity.Name),
                package.Revision,
                package.Target,
                VersionDependencyKind.PackageDependsOn));
        }

        foreach (var consumer in consumers)
        {
            additionalEdges.Add(ExactEdge(
                string.Concat(
                    "consumer-",
                    consumer.Revision.Identity.Name),
                consumer.Revision,
                consumer.Package,
                VersionDependencyKind.PackageDependsOn));
        }

        for (var index = 0; index < hostKinds.Length; index++)
        {
            additionalEdges.Add(ExactEdge(
                string.Concat("publish-profile-", hostKinds[index]),
                profiles[index],
                generatedHost,
                VersionDependencyKind.ConfiguredBy));
            additionalEdges.Add(ExactEdge(
                string.Concat("publish-leaf-", hostKinds[index]),
                leaves[index],
                profiles[index],
                VersionDependencyKind.GeneratedBy));
            additionalEdges.Add(ExactEdge(
                string.Concat("publish-manifest-", hostKinds[index]),
                manifests[index],
                leaves[index],
                VersionDependencyKind.Projects));
        }

        var mapReference = Reference(
            "version-map",
            "observatory-package-publish-extension",
            "3.0.0");
        var selectionReference = Reference(
            "version-selection",
            "observatory-package-publish-extension",
            "3.0.0");
        var selections = baseline.VersionSelection.Selections
            .AddRange(additionalNodes.Select(node =>
                new VersionSelection(
                    node.Revision.Identity,
                    node.Revision,
                    node.Revision,
                    Owner)));
        var decisions = baseline.Decisions.AddRange(
            additionalNodes.Select(node => Decision(
                node.Revision,
                ActionsFor(node.Kind))));
        return new MigrationAssessmentRequest(
            mapReference,
            selectionReference,
            new VersionMapDocument(
                baseline.VersionMap.Nodes.AddRange(additionalNodes),
                baseline.VersionMap.Edges.AddRange(additionalEdges)),
            new VersionSelectionDocument(mapReference, selections),
            decisions,
            new MigrationAnalysisLimits(64, 4096));
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

    private static ImmutableArray<MigrationRequiredAction> ActionsFor(
        VersionBoundaryKind kind) =>
        kind switch
        {
            VersionBoundaryKind.Package =>
            [
                MigrationRequiredAction.RepackageOrRelock,
                MigrationRequiredAction.Retest,
            ],
            VersionBoundaryKind.ExternalConsumer =>
            [
                MigrationRequiredAction.Recompile,
                MigrationRequiredAction.Retest,
            ],
            VersionBoundaryKind.Configuration =>
            [
                MigrationRequiredAction.Regenerate,
                MigrationRequiredAction.Retest,
            ],
            VersionBoundaryKind.GeneratedArtifact =>
            [
                MigrationRequiredAction.Regenerate,
                MigrationRequiredAction.Recompile,
                MigrationRequiredAction.RepackageOrRelock,
                MigrationRequiredAction.Retest,
            ],
            VersionBoundaryKind.Artifact =>
            [
                MigrationRequiredAction.Regenerate,
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

    private static VersionDependencyEdge ExactEdge(
        string name,
        ArtifactReference source,
        ArtifactReference resolution,
        VersionDependencyKind kind) =>
        new(
            new ProgramKitIdentifier(string.Concat("pkid:edge:fixture:", name)),
            source,
            resolution.Identity,
            kind,
            new SemanticVersionRange(string.Concat(
                "[",
                resolution.Version.Value,
                "]")),
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

    private static ArtifactReference PackageRevision(
        string packageId,
        string version,
        string scope) =>
        ObservatoryRevisions.Reference(
            string.Concat(
                "pkid:package:",
                scope,
                ":",
                packageId.Replace('.', '-').ToLowerInvariant()),
            version);
}
