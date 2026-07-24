using Orbyss.ProgramKit.Artifacts.Migrations;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.Workbench.Operations.Migrations;
using ObservatoryScheduling.Tests.Configuration;

namespace ObservatoryScheduling.Tests.Operations.Migrations;

public sealed class MigrationTests
{
    [Test]
    public void V1ToV2MigrationComputesTheCompleteReverseClosureAndSafeWaves()
    {
        var request = ObservatoryMigrationFixture.CreateAssessmentRequest();
        var result = CreateEngine().Assess(request);

        FixtureAssert.IsValid(result.Validation);
        FixtureAssert.IsNotNull(result.Value);
        FixtureAssert.HasCount(8, result.Value!.Impacts);
        FixtureAssert.HasCount(8, result.Value.Impacts
            .Select(static impact => impact.Observed.Identity.Value)
            .Distinct(StringComparer.Ordinal)
            .ToArray());
        FixtureAssert.IsTrue(result.Value.Impacts.All(static impact =>
            impact.Disposition ==
            MigrationTerminalDisposition.CompatibleAfterActions));
        FixtureAssert.IsTrue(result.Value.Impacts.All(static impact =>
            !impact.RequiredActions.IsDefaultOrEmpty));
        FixtureAssert.IsTrue(result.Value.Waves.Length >= 5);
        FixtureAssert.AreEqual(
            "schema",
            result.Value.Waves[0].Cohorts[0].Members[0].Identity.Kind);
        FixtureAssert.IsTrue(result.Value.Impacts.Single(static impact =>
            impact.Observed.Identity.Kind == "host").RequiredActions
            .SequenceEqual(
            [
                MigrationRequiredAction.Regenerate,
                MigrationRequiredAction.Recompile,
                MigrationRequiredAction.RepackageOrRelock,
                MigrationRequiredAction.Retest,
            ]));
    }

    [Test]
    public void PendingWorkPolicyDrainsV1AndRejectsTheV2Handler()
    {
        var policy = ObservatoryMigrationFixture.CreatePendingWorkPolicy();

        FixtureAssert.AreEqual(
            PendingWorkDisposition.DrainObservedRevision,
            policy.Disposition);
        FixtureAssert.IsFalse(policy.AllowObservedInstanceOnTargetHandler);
        FixtureAssert.AreEqual(
            "1.0.0",
            policy.ObservedTaskDefinition.Version.Value);
        FixtureAssert.AreEqual(
            "2.0.0",
            policy.TargetTaskDefinition.Version.Value);
        FixtureAssert.AreEqual(
            policy.ObservedTaskDefinition.Identity,
            policy.TargetTaskDefinition.Identity);
    }

    [Test]
    public void PackagePublishExtensionRerunsTheCompleteMigrationClosure()
    {
        var request =
            ObservatoryMigrationFixture.CreatePackagePublishAssessmentRequest();
        var result = CreateEngine().Assess(request);

        FixtureAssert.IsValid(result.Validation);
        FixtureAssert.IsNotNull(result.Value);
        FixtureAssert.HasCount(28, result.Value!.Impacts);
        FixtureAssert.HasCount(
            6,
            request.VersionMap.Nodes.Where(static node =>
                node.Kind == VersionBoundaryKind.Package).ToArray());
        FixtureAssert.HasCount(
            5,
            request.VersionMap.Nodes.Where(static node =>
                node.Kind == VersionBoundaryKind.ExternalConsumer).ToArray());
        FixtureAssert.HasCount(
            3,
            request.VersionMap.Nodes.Where(static node =>
                node.Revision.Identity.Kind == "publish-profile").ToArray());
        FixtureAssert.HasCount(
            3,
            request.VersionMap.Nodes.Where(static node =>
                node.Revision.Identity.Kind == "publish-leaf").ToArray());
        FixtureAssert.HasCount(
            3,
            request.VersionMap.Nodes.Where(static node =>
                node.Revision.Identity.Kind == "local-publish-manifest")
                .ToArray());
        FixtureAssert.IsTrue(result.Value.Impacts.All(static impact =>
            impact.Disposition ==
            MigrationTerminalDisposition.CompatibleAfterActions));
        FixtureAssert.IsTrue(result.Value.Impacts.All(static impact =>
            !impact.RequiredActions.IsDefaultOrEmpty &&
            !impact.RequiredEvidence.IsDefaultOrEmpty));
    }

    private static MigrationAssessmentEngine CreateEngine()
    {
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        return new MigrationAssessmentEngine(
            new VersionMapDocumentValidator(envelopeValidator),
            new VersionSelectionDocumentValidator(envelopeValidator),
            new MigrationAssessmentValidator(envelopeValidator));
    }
}
