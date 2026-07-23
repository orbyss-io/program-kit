using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Planning;
using Orbyss.ProgramKit.Quality;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class ApprovalGateTests
{
    [TestMethod]
    public void ExactUnconditionalActiveHumanApprovalHasAValidRelationship()
    {
        var plan = CreatePlan();
        var approval = CreateApproval(plan, PlanReference);

        var validation = DesignPlanApprovalRelationshipValidator.Validate(
            plan,
            PlanReference,
            DesignReference,
            approval);

        Assert.IsTrue(
            validation.IsValid,
            string.Join(
                Environment.NewLine,
                validation.Diagnostics.Select(diagnostic => diagnostic.Message)));
    }

    [TestMethod]
    public void MissingChangedRejectedConditionalAndSupersededApprovalFailClosed()
    {
        var plan = CreatePlan();
        var approval = CreateApproval(plan, PlanReference);
        var changedDesign = TestContractValues.Reference(
            "pkid:design:program-kit:changed-design");
        var rejected = approval with
        {
            Decision = DesignPlanApprovalDecision.Rejected,
        };
        var conditional = approval with
        {
            Conditions =
            [
                new ApprovalCondition(
                    "human-review",
                    "A human review remains open.",
                    ApprovalConditionState.Open,
                    null),
            ],
        };
        var superseded = approval with
        {
            Supersession = new ApprovalSupersession(
                ApprovalSupersessionState.Superseded,
                TestContractValues.Reference(
                    "pkid:approval:program-kit:replacement-approval")),
        };

        Assert.IsFalse(DesignPlanApprovalRelationshipValidator.Validate(
            plan,
            PlanReference,
            DesignReference,
            null).IsValid);
        Assert.IsFalse(DesignPlanApprovalRelationshipValidator.Validate(
            plan,
            PlanReference,
            changedDesign,
            approval).IsValid);
        Assert.IsFalse(DesignPlanApprovalRelationshipValidator.Validate(
            plan,
            PlanReference,
            DesignReference,
            rejected).IsValid);
        Assert.IsFalse(DesignPlanApprovalRelationshipValidator.Validate(
            plan,
            PlanReference,
            DesignReference,
            conditional).IsValid);
        Assert.IsFalse(DesignPlanApprovalRelationshipValidator.Validate(
            plan,
            PlanReference,
            DesignReference,
            superseded).IsValid);
    }

    [TestMethod]
    public void ChangingOnlyTheDesignDigestInvalidatesTheExactApprovalRelationship()
    {
        var plan = CreatePlan();
        var approval = CreateApproval(plan, PlanReference);
        var changedDigest = DesignReference with
        {
            Digest = Sha256Digest.Parse(
                string.Concat("sha256:", new string('b', 64))),
        };

        var validation = DesignPlanApprovalRelationshipValidator.Validate(
            plan,
            PlanReference,
            changedDigest,
            approval);

        Assert.IsFalse(validation.IsValid);
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln301));
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln305));
    }

    [TestMethod]
    public void EveryDeclaredRequirementRequiresItsOwnTraceDisposition()
    {
        var incomplete = CreatePlan() with
        {
            RequirementIds = ["PK-R001", "PK-R002"],
        };

        var validation = new ImplementationPlanDocumentValidator().Validate(incomplete);

        Assert.IsFalse(validation.IsValid);
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln127));
    }

    [TestMethod]
    public void ApprovalCannotSupersedeItselfByExactDigestReference()
    {
        var selfReference = TestContractValues.Reference(
            "pkid:approval:program-kit:self-referencing-approval");
        var plan = CreatePlan();
        var approval = CreateApproval(plan, PlanReference) with
        {
            Supersession = new ApprovalSupersession(
                ApprovalSupersessionState.Superseded,
                selfReference),
        };
        var envelope = TestContractValues.Envelope(
            selfReference.Identity.Value,
            "approval",
            approval);

        var validation = new DesignPlanApprovalRecordValidator().Validate(envelope);

        Assert.IsFalse(validation.IsValid);
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln219 &&
            diagnostic.Path == "/document/supersession/supersededBy"));
    }

    [TestMethod]
    public void UnknownPlanningEnumsFailClosed()
    {
        var plan = CreatePlan() with
        {
            State = (ImplementationPlanState)int.MaxValue,
        };
        var approval = CreateApproval(plan, PlanReference) with
        {
            Decision = (DesignPlanApprovalDecision)int.MaxValue,
            Conditions =
            [
                new ApprovalCondition(
                    "unknown-state",
                    "The state is intentionally invalid.",
                    (ApprovalConditionState)int.MaxValue,
                    null),
            ],
            Supersession = new ApprovalSupersession(
                (ApprovalSupersessionState)int.MaxValue,
                null),
        };

        var planValidation = new ImplementationPlanDocumentValidator().Validate(plan);
        var approvalValidation =
            new DesignPlanApprovalRecordValidator().Validate(approval);

        Assert.IsTrue(planValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln141));
        Assert.IsTrue(approvalValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln216));
        Assert.IsTrue(approvalValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln217));
        Assert.IsTrue(approvalValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln218));
    }

    [TestMethod]
    public void PlanRejectsWrongMigrationTestAndProfileKinds()
    {
        var plan = CreatePlan();
        var invalidWorkUnit = plan.WorkUnits[0] with
        {
            Migrations =
            [
                TestContractValues.Reference(
                    "pkid:package:program-kit:not-a-migration"),
            ],
            SelectedTests =
            [
                new TestSpecificationSelection(
                    TestContractValues.Reference(
                        "pkid:test-specification:program-kit:not-a-test"),
                    TestContractValues.Profile(
                        "pkid:execution-profile:program-kit:not-a-profile")),
            ],
        };
        var invalid = plan with
        {
            WorkUnits = [invalidWorkUnit],
        };

        var validation = new ImplementationPlanDocumentValidator().Validate(invalid);

        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln014));
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln015));
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == PlanningDiagnosticIds.Pkpln016));
    }

    private static ArtifactReference PlanReference =>
        TestContractValues.Reference("pkid:plan:program-kit:test-plan");

    private static ArtifactReference DesignReference =>
        TestContractValues.Reference("pkid:design:program-kit:test-design");

    private static ImplementationPlanDocument CreatePlan()
    {
        var designReference = DesignReference;
        var owner = ProgramKitIdentifier.Parse(
            "pkid:domain:program-kit:planning");
        var output = TestContractValues.Reference(
            "pkid:contract:program-kit:test-output");

        return new ImplementationPlanDocument(
            designReference,
            owner,
            ImplementationPlanState.ReadyForHumanDecision,
            ["PK-R001"],
            [
                new PlanWorkUnit(
                    "PK-W010",
                    "Implement the bounded test output.",
                    0,
                    null,
                    [],
                    [designReference],
                    [output],
                    ["program-kit/"],
                    [],
                    [],
                    [],
                    [],
                    ["Stop on architectural deviation."],
                    [
                        new PlanVerificationCommand(
                            "dotnet",
                            ["test"],
                            "program-kit",
                            "All selected tests pass."),
                    ],
                    []),
            ],
            [],
            [
                new RequirementTrace(
                    "PK-R001",
                    owner,
                    output,
                    ["PK-W010"],
                    "The contract is implemented.",
                    [],
                    [],
                    [],
                    "A consumer validates the contract."),
            ],
            []);
    }

    private static DesignPlanApprovalRecord CreateApproval(
        ImplementationPlanDocument plan,
        ArtifactReference planReference)
    {
        return new DesignPlanApprovalRecord(
            plan.Design,
            planReference,
            "The exact bounded test plan.",
            new PrincipalReference(
                "human-session-participant",
                "test",
                "human-1",
                "human-requester"),
            new AuthorityReference(
                "test-approval-boundary",
                TestContractValues.Reference(
                    "pkid:approval:program-kit:test-boundary"),
                "/approvalBoundary",
                ProgramKitIdentifier.Parse(
                    "pkid:domain:program-kit:planning")),
            [
                new HumanDecisionEvidence(
                    "human-session-statement",
                    "test",
                    "decision-1",
                    TestContractValues.Digest),
            ],
            "approval-correlation",
            new DateTimeOffset(2026, 7, 23, 8, 0, 0, TimeSpan.Zero),
            DesignPlanApprovalDecision.Approved,
            [],
            new ApprovalSupersession(
                ApprovalSupersessionState.Active,
                null));
    }
}
