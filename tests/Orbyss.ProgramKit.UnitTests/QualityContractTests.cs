using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Quality;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class QualityContractTests
{
    [TestMethod]
    public void ExactSelectionAcceptsAProfileThatClosesRequirements()
    {
        var dependency = TestContractValues.Reference(
            "pkid:package:program-kit:required-dependency");
        var specification = CreateSpecification(dependency);
        var profile = CreateProfile(dependency);
        var selection = new TestSpecificationSelection(
            SpecificationReference,
            ProfileReference);

        var result = TestExecutionSelectionValidator.Validate(
            specification,
            SpecificationReference,
            profile,
            ProfileReference,
            selection);

        Assert.IsTrue(result.IsValid, Format(result));
    }

    [TestMethod]
    public void SelectionFailsWhenTheExactDependencyClosureIsIncomplete()
    {
        var dependency = TestContractValues.Reference(
            "pkid:package:program-kit:required-dependency");
        var specification = CreateSpecification(dependency);
        var profile = CreateProfile();
        var selection = new TestSpecificationSelection(
            SpecificationReference,
            ProfileReference);

        var result = TestExecutionSelectionValidator.Validate(
            specification,
            SpecificationReference,
            profile,
            ProfileReference,
            selection);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic => diagnostic.Id == "PKQLT205"));
    }

    [TestMethod]
    public void SelectionFailsWhenEitherExactBindingDiffers()
    {
        var dependency = TestContractValues.Reference(
            "pkid:package:program-kit:required-dependency");
        var specification = CreateSpecification(dependency);
        var profile = CreateProfile(dependency);
        var selection = new TestSpecificationSelection(
            TestContractValues.Reference(
                "pkid:test:program-kit:different-specification"),
            TestContractValues.Profile(
                "pkid:profile:program-kit:different-profile"));

        var result = TestExecutionSelectionValidator.Validate(
            specification,
            SpecificationReference,
            profile,
            ProfileReference,
            selection);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic => diagnostic.Id == "PKQLT201"));
        Assert.IsTrue(result.Diagnostics.Any(diagnostic => diagnostic.Id == "PKQLT202"));
    }

    [TestMethod]
    public void EvidenceMustBindTheExactSelectionAndRequiredObservationShape()
    {
        var dependency = TestContractValues.Reference(
            "pkid:package:program-kit:required-dependency");
        var specification = CreateSpecification(dependency);
        var profile = CreateProfile(dependency);
        var evidence = new TestEvidence(
            SpecificationReference,
            ProfileReference,
            TestContractValues.Reference("pkid:subject:program-kit:tested-subject"),
            TestEvidenceOutcome.Passed,
            [new TestObservation("exit-code", "0", null)],
            ProgramKitIdentifier.Parse("pkid:producer:program-kit:test-runner"),
            new DateTimeOffset(2026, 7, 23, 8, 0, 0, TimeSpan.Zero),
            "quality-contract-test");

        var valid = new TestEvidenceValidator().ValidateAgainst(
            evidence,
            specification,
            SpecificationReference,
            profile,
            ProfileReference);
        var wrongBindingAndShape = evidence with
        {
            Specification = TestContractValues.Reference(
                "pkid:test:program-kit:different-specification"),
            Observations = [new TestObservation("unexpected", "value", null)],
        };
        var invalid = new TestEvidenceValidator().ValidateAgainst(
            wrongBindingAndShape,
            specification,
            SpecificationReference,
            profile,
            ProfileReference);

        Assert.IsTrue(valid.IsValid, Format(valid));
        Assert.IsFalse(invalid.IsValid);
        Assert.IsTrue(invalid.Diagnostics.Any(diagnostic => diagnostic.Id == "PKQLT305"));
        Assert.IsTrue(invalid.Diagnostics.Any(diagnostic => diagnostic.Id == "PKQLT307"));
    }

    [TestMethod]
    public void EnvelopedProfileRejectsAnExactReferenceToItsOwnRevision()
    {
        var selfReference = TestContractValues.Reference(
            "pkid:profile:program-kit:self-referencing-profile");
        var profile = CreateProfile(selfReference);
        var envelope = TestContractValues.Envelope(
            selfReference.Identity.Value,
            "profile",
            profile);

        var validation = new ExecutionProfileValidator().Validate(envelope);

        Assert.IsFalse(validation.IsValid);
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt409 &&
            diagnostic.Path == "/document/dependencyClosure/0"));
    }

    [TestMethod]
    public void UnknownQualityEnumsFailClosed()
    {
        var dependency = TestContractValues.Reference(
            "pkid:package:program-kit:required-dependency");
        var specification = CreateSpecification(dependency) with
        {
            Categories = [(TestCategory)int.MaxValue],
            Scenarios =
            [
                new TestScenario(
                    "unknown-kind",
                    (TestScenarioKind)int.MaxValue,
                    "Exercise fail-closed enum handling.",
                    [],
                    [],
                    "Validation fails."),
            ],
        };
        var profile = CreateProfile(dependency) with
        {
            Access = new TestExecutionAccessPolicy(
                (NetworkAccessPolicy)int.MaxValue,
                [],
                (WriteAccessPolicy)int.MaxValue,
                [],
                (RestoreAccessPolicy)int.MaxValue,
                (SecretAccessPolicy)int.MaxValue,
                []),
        };

        var specificationValidation =
            new TestSpecificationValidator().Validate(specification);
        var profileValidation = new ExecutionProfileValidator().Validate(profile);

        Assert.IsFalse(specificationValidation.IsValid);
        Assert.IsTrue(specificationValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt110));
        Assert.IsTrue(specificationValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt111));
        Assert.IsFalse(profileValidation.IsValid);
        Assert.IsTrue(profileValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt028));
        Assert.IsTrue(profileValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt029));
        Assert.IsTrue(profileValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt030));
        Assert.IsTrue(profileValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt031));
    }

    [TestMethod]
    public void SelectionAndEvidenceRejectNoncanonicalTestAndProfileKinds()
    {
        var dependency = TestContractValues.Reference(
            "pkid:package:program-kit:required-dependency");
        var specification = CreateSpecification(dependency);
        var profile = CreateProfile(dependency);
        var wrongSpecification = TestContractValues.Reference(
            "pkid:test-specification:program-kit:wrong-kind");
        var wrongProfile = TestContractValues.Profile(
            "pkid:execution-profile:program-kit:wrong-kind");
        var selection = new TestSpecificationSelection(
            wrongSpecification,
            wrongProfile);
        var evidence = new TestEvidence(
            wrongSpecification,
            wrongProfile,
            TestContractValues.Reference("pkid:subject:program-kit:tested-subject"),
            TestEvidenceOutcome.Passed,
            [new TestObservation("exit-code", "0", null)],
            ProgramKitIdentifier.Parse("pkid:producer:program-kit:test-runner"),
            new DateTimeOffset(2026, 7, 23, 8, 0, 0, TimeSpan.Zero),
            "wrong-kind-evidence");

        var selectionValidation = TestExecutionSelectionValidator.Validate(
            specification,
            wrongSpecification,
            profile,
            wrongProfile,
            selection);
        var evidenceValidation = new TestEvidenceValidator().Validate(evidence);

        Assert.IsTrue(selectionValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt032));
        Assert.IsTrue(selectionValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt033));
        Assert.IsTrue(evidenceValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt032));
        Assert.IsTrue(evidenceValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt033));
    }

    [TestMethod]
    public void TestEvidenceShapeRejectsANonSchemaReference()
    {
        var dependency = TestContractValues.Reference(
            "pkid:package:program-kit:required-dependency");
        var specification = CreateSpecification(dependency) with
        {
            EvidenceShape = new TestEvidenceShape(
                TestContractValues.Reference(
                    "pkid:contract:program-kit:not-a-schema"),
                ["exit-code"],
                false),
        };

        var validation = new TestSpecificationValidator().Validate(specification);

        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == QualityDiagnosticIds.Pkqlt034));
    }

    private static ArtifactReference SpecificationReference =>
        TestContractValues.Reference(
            "pkid:test:program-kit:quality-contract");

    private static ProfileReference ProfileReference =>
        TestContractValues.Profile(
            "pkid:profile:program-kit:quality-contract");

    private static TestSpecification CreateSpecification(
        ArtifactReference dependency)
    {
        var access = new TestExecutionAccessPolicy(
            NetworkAccessPolicy.Denied,
            [],
            WriteAccessPolicy.TemporaryOutputOnly,
            [],
            RestoreAccessPolicy.LockedOnly,
            SecretAccessPolicy.Denied,
            []);

        return new TestSpecification(
            ProgramKitIdentifier.Parse("pkid:domain:program-kit:quality"),
            "Verify an exact quality contract.",
            ["PK-R001"],
            [TestCategory.ContractConformance],
            [
                new TestScenario(
                    "exact-selection",
                    TestScenarioKind.Positive,
                    "Exercise exact selection.",
                    [],
                    [],
                    "The selected execution succeeds."),
            ],
            new TestExecutionRequirements(
                ["dotnet-test"],
                ["windows-x64"],
                ["sdk-10.0.302"],
                [dependency],
                access,
                TimeSpan.FromMinutes(2),
                new TestRetryPolicy(1, TimeSpan.Zero)),
            new TestExpectedResult("passed", "The contract passes."),
            new TestEvidenceShape(
                TestContractValues.Reference(
                    "pkid:schema:program-kit:test-evidence"),
                ["exit-code"],
                false));
    }

    private static ExecutionProfile CreateProfile(
        params ArtifactReference[] dependencies) =>
        new(
            "dotnet-test",
            "windows-x64",
            ["sdk-10.0.302"],
            [.. dependencies],
            new TestExecutionAccessPolicy(
                NetworkAccessPolicy.Denied,
                [],
                WriteAccessPolicy.TemporaryOutputOnly,
                [],
                RestoreAccessPolicy.LockedOnly,
                SecretAccessPolicy.Denied,
                []),
            TimeSpan.FromMinutes(1),
            new TestRetryPolicy(1, TimeSpan.Zero));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
