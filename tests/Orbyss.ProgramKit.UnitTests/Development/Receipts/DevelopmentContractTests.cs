using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Capabilities;
using Orbyss.ProgramKit.Development.Diagnostics;
using Orbyss.ProgramKit.Development.Receipts;
using Orbyss.ProgramKit.Development.Routing;
using Orbyss.ProgramKit.Development.Validation;
using Orbyss.ProgramKit.Planning.Approvals;

namespace Orbyss.ProgramKit.UnitTests.Development.Receipts;

[TestClass]
public sealed class DevelopmentContractTests
{
    private static readonly string[] RoutingOutcomePropertyNames =
        ["Kind", "NextCapabilities", "Reason"];

    [TestMethod]
    public void RoutingSelectsZeroOrOneCapabilityFromTheExactAvailabilitySnapshot()
    {
        var capability = TestContractValues.Reference(
            "pkid:capability:program-kit:implement-software-plan");
        var snapshot = CreateSnapshot(
            new CapabilityAvailability(
                capability.Identity,
                CapabilityAvailabilityStatus.Available));
        var outcome = new DevelopmentRoutingOutcome(
            DevelopmentRoutingOutcomeKind.Routed,
            [capability],
            "The requested capability is available.");
        var result = new DevelopmentRoutingResult(
            TestContractValues.Reference("pkid:intent:program-kit:bootstrap"),
            SnapshotReference,
            outcome);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        DevelopmentRoutingOutcomeValidator outcomeValidator =
            new DevelopmentRoutingOutcomeValidator();
        CapabilityAvailabilitySnapshotValidator snapshotValidator =
            new CapabilityAvailabilitySnapshotValidator(envelopeValidator);
        var routingResultValidator = new DevelopmentRoutingResultValidator(
            outcomeValidator,
            snapshotValidator,
            envelopeValidator);

        var validation = routingResultValidator.ValidateAgainst(
            result,
            snapshot,
            SnapshotReference);

        Assert.IsTrue(validation.IsValid, Format(validation));
    }

    [TestMethod]
    public void RoutingRejectsMultipleOrUnavailableCapabilities()
    {
        var first = TestContractValues.Reference(
            "pkid:capability:program-kit:first-capability");
        var second = TestContractValues.Reference(
            "pkid:capability:program-kit:second-capability");
        var tooMany = new DevelopmentRoutingOutcome(
            DevelopmentRoutingOutcomeKind.Routed,
            [first, second],
            "Two candidates were selected.");
        var snapshot = CreateSnapshot(
            new CapabilityAvailability(
                first.Identity,
                CapabilityAvailabilityStatus.Unavailable));
        var unavailableResult = new DevelopmentRoutingResult(
            TestContractValues.Reference("pkid:intent:program-kit:bootstrap"),
            SnapshotReference,
            new DevelopmentRoutingOutcome(
                DevelopmentRoutingOutcomeKind.Routed,
                [first],
                "The candidate was selected."));
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        DevelopmentRoutingOutcomeValidator outcomeValidator =
            new DevelopmentRoutingOutcomeValidator();
        CapabilityAvailabilitySnapshotValidator snapshotValidator =
            new CapabilityAvailabilitySnapshotValidator(envelopeValidator);
        var routingResultValidator = new DevelopmentRoutingResultValidator(
            outcomeValidator,
            snapshotValidator,
            envelopeValidator);

        var cardinality = outcomeValidator.Validate(tooMany);
        var availability = routingResultValidator.ValidateAgainst(
            unavailableResult,
            snapshot,
            SnapshotReference);

        Assert.IsFalse(cardinality.IsValid);
        Assert.IsTrue(cardinality.Diagnostics.Any(diagnostic => diagnostic.Id == "PKDEV201"));
        Assert.IsFalse(availability.IsValid);
        Assert.IsTrue(availability.Diagnostics.Any(diagnostic => diagnostic.Id == "PKDEV206"));
    }

    [TestMethod]
    public void HumanDecisionAndUnavailableOutcomesCannotDelegateANextCapability()
    {
        var capability = TestContractValues.Reference(
            "pkid:capability:program-kit:implement-software-plan");
        var humanDecision = new DevelopmentRoutingOutcome(
            DevelopmentRoutingOutcomeKind.HumanDecisionRequired,
            [capability],
            "A human decision is required.");
        var unavailable = new DevelopmentRoutingOutcome(
            DevelopmentRoutingOutcomeKind.FlowUnavailable,
            [capability],
            "The flow is unavailable.");
        DevelopmentRoutingOutcomeValidator outcomeValidator =
            new DevelopmentRoutingOutcomeValidator();

        var humanDecisionResult = outcomeValidator.Validate(humanDecision);
        var unavailableResult = outcomeValidator.Validate(unavailable);

        Assert.IsTrue(
            humanDecisionResult.Diagnostics.Any(diagnostic => diagnostic.Id == "PKDEV202"));
        Assert.IsTrue(
            unavailableResult.Diagnostics.Any(diagnostic => diagnostic.Id == "PKDEV202"));
    }

    [TestMethod]
    public void RoutingContractsContainNoAuthorityGrant()
    {
        var routingProperties = typeof(DevelopmentRoutingOutcome)
            .GetProperties()
            .Select(property => property.Name)
            .ToArray();
        var resultProperties = typeof(DevelopmentRoutingResult)
            .GetProperties()
            .Select(property => property.Name)
            .ToArray();

        Assert.DoesNotContain(
            static property =>
                property.Contains("Authority", StringComparison.Ordinal),
            routingProperties.Concat(resultProperties));
        Assert.AreSequenceEqual(
            RoutingOutcomePropertyNames,
            routingProperties,
            SequenceOrder.InAnyOrder);
    }

    [TestMethod]
    public void ReceiptIsEvidenceBoundToExactInputsAndAnExplicitTimeBoundary()
    {
        var suppliedAt =
            new DateTimeOffset(2026, 7, 23, 8, 0, 0, TimeSpan.Zero);
        var receipt = new DevelopmentReceipt(
            TestContractValues.Reference(
                "pkid:capability:program-kit:implement-software-plan"),
            TestContractValues.Reference(
                "pkid:intent:program-kit:bootstrap"),
            [
                TestContractValues.Reference(
                    "pkid:plan:program-kit:bootstrap-plan"),
            ],
            new DevelopmentResult(
                DevelopmentResultKind.Completed,
                "The bounded capability completed.",
                [
                    TestContractValues.Reference(
                        "pkid:evidence:program-kit:bootstrap-result"),
                ],
                null),
            ProgramKitIdentifier.Parse(
                "pkid:producer:program-kit:human-session-boundary"),
            new PrincipalReference(
                "human-session-participant",
                "test",
                "human-1",
                "human-requester"),
            "development-receipt-test",
            suppliedAt);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        DevelopmentRoutingOutcomeValidator outcomeValidator =
            new DevelopmentRoutingOutcomeValidator();
        var validator = new DevelopmentReceiptValidator(
            outcomeValidator,
            envelopeValidator);

        var valid = validator.ValidateNotBefore(
            receipt,
            suppliedAt - TimeSpan.FromSeconds(1));
        var backdated = validator.ValidateNotBefore(
            receipt,
            suppliedAt + TimeSpan.FromSeconds(1));

        Assert.IsTrue(valid.IsValid, Format(valid));
        Assert.IsFalse(backdated.IsValid);
        Assert.IsTrue(backdated.Diagnostics.Any(diagnostic => diagnostic.Id == "PKDEV302"));
        Assert.DoesNotContain(
            static property =>
                property.Name.Contains("Authority", StringComparison.Ordinal),
            typeof(DevelopmentReceipt).GetProperties());
    }

    [TestMethod]
    public void EnvelopedRoutingRejectsAnExactReferenceToItsOwnRevision()
    {
        var selfReference = TestContractValues.Reference(
            "pkid:routing-result:program-kit:self-referencing-routing");
        var result = new DevelopmentRoutingResult(
            selfReference,
            SnapshotReference,
            new DevelopmentRoutingOutcome(
                DevelopmentRoutingOutcomeKind.FlowUnavailable,
                [],
                "No supported flow is available."));
        var envelope = TestContractValues.Envelope(
            selfReference.Identity.Value,
            "routing-result",
            result);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        DevelopmentRoutingOutcomeValidator outcomeValidator =
            new DevelopmentRoutingOutcomeValidator();
        CapabilityAvailabilitySnapshotValidator snapshotValidator =
            new CapabilityAvailabilitySnapshotValidator(envelopeValidator);
        var routingResultValidator = new DevelopmentRoutingResultValidator(
            outcomeValidator,
            snapshotValidator,
            envelopeValidator);

        var validation = routingResultValidator.Validate(envelope);

        Assert.IsFalse(validation.IsValid);
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == DevelopmentDiagnosticIds.Pkdev307 &&
            diagnostic.Path == "/document/requestOrIntent"));
    }

    [TestMethod]
    public void UnknownDevelopmentEnumsFailClosed()
    {
        var capability = TestContractValues.Reference(
            "pkid:capability:program-kit:unknown-status");
        var snapshot = CreateSnapshot(
            new CapabilityAvailability(
                capability.Identity,
                (CapabilityAvailabilityStatus)int.MaxValue));
        var routing = new DevelopmentRoutingOutcome(
            (DevelopmentRoutingOutcomeKind)int.MaxValue,
            [],
            "The outcome kind is invalid.");
        var result = new DevelopmentResult(
            (DevelopmentResultKind)int.MaxValue,
            "The result kind is invalid.",
            [],
            routing);
        var receipt = new DevelopmentReceipt(
            capability,
            TestContractValues.Reference("pkid:intent:program-kit:unknown-enums"),
            [],
            result,
            ProgramKitIdentifier.Parse("pkid:producer:program-kit:test"),
            new PrincipalReference(
                "human-session-participant",
                "test",
                "human-1",
                "human-requester"),
            "unknown-enums",
            new DateTimeOffset(2026, 7, 23, 8, 0, 0, TimeSpan.Zero));
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        DevelopmentRoutingOutcomeValidator outcomeValidator =
            new DevelopmentRoutingOutcomeValidator();
        CapabilityAvailabilitySnapshotValidator snapshotValidator =
            new CapabilityAvailabilitySnapshotValidator(envelopeValidator);
        DevelopmentReceiptValidator receiptValidator =
            new DevelopmentReceiptValidator(
                outcomeValidator,
                envelopeValidator);

        var snapshotValidation = snapshotValidator.Validate(snapshot);
        var receiptValidation = receiptValidator.Validate(receipt);

        Assert.IsTrue(snapshotValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == DevelopmentDiagnosticIds.Pkdev107));
        Assert.IsTrue(receiptValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == DevelopmentDiagnosticIds.Pkdev207));
        Assert.IsTrue(receiptValidation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == DevelopmentDiagnosticIds.Pkdev305));
    }

    private static ArtifactReference SnapshotReference =>
        TestContractValues.Reference(
            "pkid:capability-snapshot:program-kit:test-availability");

    private static CapabilityAvailabilitySnapshot CreateSnapshot(
        params CapabilityAvailability[] capabilities) =>
        new(
            CapabilityAvailabilitySnapshotValidator.CanonicalIndexPath,
            TestContractValues.Digest,
            [.. capabilities],
            ProgramKitIdentifier.Parse(
                "pkid:supplier:program-kit:human-session"),
            new DateTimeOffset(2026, 7, 23, 7, 59, 0, TimeSpan.Zero));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
