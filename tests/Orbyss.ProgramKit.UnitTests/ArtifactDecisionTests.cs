using System.Collections.Immutable;
using Orbyss.ProgramKit.Architecture;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class ArtifactDecisionTests
{
    [TestMethod]
    public void CompleteNineQuestionDecisionIsValid()
    {
        var decision = CreateValidDecision();

        var result = new ArtifactDecisionValidator().Validate(decision);

        Assert.IsTrue(
            result.IsValid,
            string.Join(Environment.NewLine, result.Diagnostics.Select(diagnostic => diagnostic.Message)));
    }

    [TestMethod]
    public void MissingMandatoryAnswerFailsClosed()
    {
        var decision = CreateValidDecision() with
        {
            ExecutableBehavior = null!,
        };

        var result = new ArtifactDecisionValidator().Validate(decision);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc301));
    }

    [TestMethod]
    public void CanonicalArtifactsCannotContainEphemeralData()
    {
        var decision = CreateValidDecision() with
        {
            DataHandling = new DataHandlingAnswer(
                false,
                "No sensitive values.",
                "No externalized values.",
                true,
                "Invocation-only value."),
        };

        var result = new ArtifactDecisionValidator().Validate(decision);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc324));
    }

    [TestMethod]
    public void EverySupportedArtifactKindHasOneDocumentedOwnershipRule()
    {
        var kinds = Enum.GetValues<SupportedArtifactKind>();
        var rules = SupportedArtifactKindOwnershipResolver.All;

        Assert.AreEqual(kinds.Length, rules.Length);
        for (var index = 0; index < kinds.Length; index++)
        {
            var rule = SupportedArtifactKindOwnershipResolver.Resolve(kinds[index]);
            Assert.AreEqual(kinds[index], rule.ArtifactKind);
            Assert.IsFalse(rule.ArtifactIdentityKinds.IsDefaultOrEmpty);
            Assert.IsFalse(rule.OwnerIdentityKinds.IsDefaultOrEmpty);
            Assert.IsFalse(string.IsNullOrWhiteSpace(rule.CanonicalOwnership));
        }
    }

    [TestMethod]
    public void SchemaArtifactCannotGovernAContractIdentity()
    {
        var decision = CreateValidDecision();
        var contractIdentity = ProgramKitIdentifier.Parse(
            "pkid:contract:program-kit:sample-contract");
        var invalid = decision with
        {
            Identity = contractIdentity,
            Governance = decision.Governance with
            {
                ArtifactIdentity = contractIdentity,
            },
        };

        var result = new ArtifactDecisionValidator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc329 &&
            diagnostic.Path == "/identity"));
    }

    [TestMethod]
    public void ArtifactOwnerMustMatchTheCanonicalOwnershipClassification()
    {
        var decision = CreateValidDecision();
        var contractOwner = ProgramKitIdentifier.Parse(
            "pkid:contract:program-kit:not-an-owner");
        var invalid = decision with
        {
            OwnerId = contractOwner,
            Governance = decision.Governance with
            {
                OwnerId = contractOwner,
            },
        };

        var result = new ArtifactDecisionValidator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc330 &&
            diagnostic.Path == "/ownerId"));
    }

    [TestMethod]
    public void SchemaInstancesIncludeCapabilityAvailabilitySnapshots()
    {
        Assert.IsTrue(
            SupportedArtifactKindOwnershipResolver.SupportsArtifactIdentity(
                SupportedArtifactKind.SchemaInstance,
                "capability-snapshot"));
    }

    private static ArtifactDecision CreateValidDecision()
    {
        var identity = ProgramKitIdentifier.Parse(
            "pkid:schema:program-kit:sample-contract");
        var owner = ProgramKitIdentifier.Parse(
            "pkid:domain:program-kit:architecture");

        return new ArtifactDecision(
            identity,
            owner,
            "Exchange a typed sample contract.",
            SupportedArtifactKind.Schema,
            new ExecutableBehaviorAnswer(false, "The schema contains no executable behavior."),
            new ValueLifecycleAnswer(
                [ValueLifecycleUse.Validated, ValueLifecycleUse.Exchanged],
                "The value is validated before exchange."),
            new AgentRetrievalAnswer(false, string.Empty, "No agent retrieval is required."),
            new AgentProcedureAnswer(
                false,
                string.Empty,
                string.Empty,
                "No agent procedure is required."),
            new HumanCommunicationAnswer(
                false,
                string.Empty,
                string.Empty,
                "The artifact is machine-readable."),
            new GeneratedNavigationAnswer(
                false,
                [],
                string.Empty,
                "No navigation projection is required."),
            new RepresentationAnswer(
                ArtifactRepresentationRole.Canonical,
                null,
                string.Empty,
                string.Empty),
            new GovernanceAnswer(
                identity,
                owner,
                null,
                "Exact source references are required.",
                "The canonical envelope is digested.",
                [ProgramKitIdentifier.Parse("pkid:project:program-kit:unit-tests")],
                "Schema majors require explicit migration.",
                "Migration emits a new artifact."),
            new DataHandlingAnswer(
                false,
                "No sensitive values.",
                "No externalized values.",
                false,
                "Canonical instances contain no ephemeral values."),
            "A schema is the canonical owner of the wire contract.");
    }
}
