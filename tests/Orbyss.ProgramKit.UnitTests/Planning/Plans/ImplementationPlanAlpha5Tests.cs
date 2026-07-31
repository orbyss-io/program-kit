using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;
using Orbyss.ProgramKit.Planning.Validation;

namespace Orbyss.ProgramKit.UnitTests.Planning.Plans;

[TestClass]
public sealed class ImplementationPlanAlpha5Tests
{
    private static readonly ArtifactReference Matrix =
        Reference("pkid:activation-matrix:consumer:build-spine");
    private static readonly ArtifactReference Profile =
        Reference("pkid:profile:consumer:build-exhaustive");
    private static readonly ArtifactReference Policy =
        Reference("pkid:contract:consumer:profile-compatibility");

    [TestMethod]
    public void ExplicitMigrationPreservesLegacyAndValidatesBothBindingModes()
    {
        var source = CreateAlpha4();
        var bindings = ImmutableArray.Create(
            new PlanWorkUnitAlpha5Binding(
                "P1",
                PlanArtifactBinding.ApprovalFixed(Matrix),
                PlanArtifactBinding.ExecutionResolved(
                    Profile.Identity,
                    new SemanticVersionRange("[1.0.0,2.0.0)"),
                    Policy)));
        var migrated = ImplementationPlanAlpha4ToAlpha5Migration.Migrate(
            source,
            bindings);
        ImplementationPlanDocumentValidator versionTwo =
            new(new DefaultArtifactEnvelopeValidator());
        ImplementationPlanDocumentAlpha4Validator legacyValidator =
            new(versionTwo);
        ImplementationPlanDocumentAlpha5Validator currentValidator =
            new(versionTwo);

        Assert.IsTrue(
            legacyValidator.Validate(source).IsValid,
            Format(legacyValidator.Validate(source)));
        Assert.IsTrue(
            currentValidator.Validate(migrated).IsValid,
            Format(currentValidator.Validate(migrated)));
        Assert.AreEqual(
            ImplementationPlanDocumentAlpha5.SchemaUri,
            migrated.Schema);
        Assert.AreEqual(
            PlanArtifactBindingResolutionMode.ApprovalFixed,
            migrated.WorkUnits[0].ActivationMatrix!.ResolutionMode);
        Assert.AreEqual(
            PlanArtifactBindingResolutionMode.ExecutionResolved,
            migrated.WorkUnits[0].VerificationProfile!.ResolutionMode);

        Assert.ThrowsExactly<ArgumentException>(() =>
            ImplementationPlanAlpha4ToAlpha5Migration.Migrate(source, []));
        Assert.ThrowsExactly<ArgumentException>(() =>
            ImplementationPlanAlpha4ToAlpha5Migration.Migrate(
                source,
                [bindings[0], bindings[0]]));
    }

    [TestMethod]
    public void ValidatorRejectsIncompleteAndRelabeledBindings()
    {
        var source = CreateAlpha4();
        var valid = ImplementationPlanAlpha4ToAlpha5Migration.Migrate(
            source,
            [
                new PlanWorkUnitAlpha5Binding(
                    "P1",
                    PlanArtifactBinding.ApprovalFixed(Matrix),
                    PlanArtifactBinding.ExecutionResolved(
                        Profile.Identity,
                        new SemanticVersionRange("[1.0.0,2.0.0)"),
                        Policy)),
            ]);
        ImplementationPlanDocumentAlpha5Validator validator =
            new(new ImplementationPlanDocumentValidator(
                new DefaultArtifactEnvelopeValidator()));
        var incomplete = valid with
        {
            WorkUnits =
            [
                valid.WorkUnits[0] with
                {
                    VerificationProfile =
                        valid.WorkUnits[0].VerificationProfile! with
                        {
                            CompatibilityPolicy = null,
                        },
                },
            ],
        };
        var relabeled = valid with
        {
            WorkUnits =
            [
                valid.WorkUnits[0] with
                {
                    ActivationMatrix =
                        valid.WorkUnits[0].ActivationMatrix! with
                        {
                            ApprovedIdentity = Matrix.Identity,
                        },
                },
            ],
        };

        var incompleteResult = validator.Validate(incomplete);
        var relabeledResult = validator.Validate(relabeled);

        Assert.IsFalse(incompleteResult.IsValid);
        Assert.IsFalse(relabeledResult.IsValid);
        Assert.IsTrue(incompleteResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln150));
        Assert.IsTrue(relabeledResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln149));
    }

    [TestMethod]
    public void ResolverRequiresExactSelectionAndCompatibilityEvidence()
    {
        var fixedBinding = PlanArtifactBinding.ApprovalFixed(Matrix);
        var resolvedBinding = PlanArtifactBinding.ExecutionResolved(
            Profile.Identity,
            new SemanticVersionRange("[1.0.0,2.0.0)"),
            Policy);
        var compatible = Profile with
        {
            Version = new SemanticVersion("1.1.0"),
            Digest = new Sha256Digest(
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
        };

        var exactFixed = PlanArtifactBindingResolver.Resolve(
            fixedBinding,
            Matrix,
            null);
        var wrongFixed = PlanArtifactBindingResolver.Resolve(
            fixedBinding,
            Matrix with
            {
                Digest = new Sha256Digest(
                    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
            },
            null);
        var exactResolved = PlanArtifactBindingResolver.Resolve(
            resolvedBinding,
            compatible,
            Policy);
        var stalePolicy = PlanArtifactBindingResolver.Resolve(
            resolvedBinding,
            compatible,
            Policy with
            {
                Digest = new Sha256Digest(
                    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
            });
        var outsideRange = PlanArtifactBindingResolver.Resolve(
            resolvedBinding,
            compatible with
            {
                Version = new SemanticVersion("2.0.0"),
            },
            Policy);
        var missingSelection = PlanArtifactBindingResolver.Resolve(
            resolvedBinding,
            null,
            Policy);

        Assert.IsTrue(exactFixed.IsResolved);
        Assert.IsFalse(wrongFixed.IsResolved);
        Assert.IsTrue(exactResolved.IsResolved);
        Assert.AreEqual(
            compatible,
            exactResolved.Receipt!.SelectedArtifact);
        Assert.AreEqual(
            Policy,
            exactResolved.Receipt.CompatibilityEvidence);
        Assert.IsFalse(stalePolicy.IsResolved);
        Assert.IsFalse(outsideRange.IsResolved);
        Assert.IsFalse(missingSelection.IsResolved);
    }

    private static ImplementationPlanDocumentAlpha4 CreateAlpha4()
    {
        var design = Reference(
            "pkid:design:consumer:software",
            "0.1.0-alpha.3");
        PlanWorkUnitV3 unit = new(
            "P1",
            "Implement the approved product.",
            10,
            null,
            [],
            [design],
            [],
            ["src/Consumer/"],
            [],
            [],
            [],
            [],
            ["Stop on material drift."],
            [
                new PlanVerificationCommand(
                    "dotnet",
                    ["test"],
                    ".",
                    "Focused tests pass."),
            ],
            [],
            PlanWorkUnitKind.Product,
            Matrix,
            Profile);
        return new ImplementationPlanDocumentAlpha4(
            ImplementationPlanDocumentAlpha4.SchemaUri,
            design,
            new ProgramKitIdentifier("pkid:domain:consumer:software"),
            ImplementationPlanState.ReadyForHumanDecision,
            ["R1"],
            [unit],
            [],
            [
                new RequirementTrace(
                    "R1",
                    new ProgramKitIdentifier("pkid:domain:consumer:software"),
                    design,
                    ["P1"],
                    "Implement the approved product.",
                    [],
                    [],
                    [],
                    "The product is implemented."),
            ],
            [],
            Reference(
                "pkid:static-conformance-disposition:consumer:software",
                "0.1.0-alpha.2"),
            StaticConformancePlanState.ReuseExisting,
            null,
            Planned("pkid:gate-definition:consumer:build"),
            Planned("pkid:selection-lock:consumer:build"),
            Planned("pkid:evidence:consumer:build-activation"));
    }

    private static PlannedArtifactReference Planned(string identity) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            PlannedArtifactState.Materialized,
            new Sha256Digest(
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"));

    private static ArtifactReference Reference(
        string identity,
        string version = "1.0.0") =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion(version),
            new Sha256Digest(
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
