using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class ArtifactEnvelopeTests
{
    private static readonly string[] ArtifactStatusNames =
        ["Implemented", "Scaffolded", "Deferred", "Aspirational"];

    [TestMethod]
    public void CompleteEnvelopeIsValid()
    {
        var envelope = CreateEnvelope();

        var result = new ArtifactEnvelopeValidator<string>().Validate(envelope);

        Assert.IsTrue(
            result.IsValid,
            string.Join(Environment.NewLine, result.Diagnostics.Select(diagnostic => diagnostic.Message)));
    }

    [TestMethod]
    public void ConditionalCompatibilityRequiresExplicitConditions()
    {
        var envelope = CreateEnvelope();
        var invalidClaim = envelope.Compatibility.Dimensions[0] with
        {
            Classification = CompatibilityClassification.ConditionallyCompatible,
            Conditions = [],
        };
        var invalid = envelope with
        {
            Compatibility = envelope.Compatibility with
            {
                Dimensions = [invalidClaim],
            },
        };

        var result = new ArtifactEnvelopeValidator<string>().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(
            diagnostic => diagnostic.Id == ArtifactDiagnosticIds.InvalidCompatibility));
    }

    [TestMethod]
    public void ReviewStateCannotBeSmuggledIntoImplementationStatus()
    {
        var names = Enum.GetNames<ArtifactStatus>();

        CollectionAssert.AreEquivalent(
            ArtifactStatusNames,
            names);
        Assert.IsFalse(names.Any(name => name.Contains("Approved", StringComparison.Ordinal)));
    }

    private static ArtifactEnvelope<string> CreateEnvelope()
    {
        var version = SemanticVersion.Parse("1.0.0");
        var exactVersion = SemanticVersionRange.Parse("[1.0.0]");

        return new ArtifactEnvelope<string>(
            new ArtifactContract(
                ProgramKitIdentifier.Parse("pkid:schema:program-kit:test-document"),
                version),
            new ArtifactIdentity(
                ProgramKitIdentifier.Parse("pkid:fixture:program-kit:test-document"),
                "schema-instance",
                version,
                ProgramKitIdentifier.Parse("pkid:domain:program-kit:artifacts"),
                ArtifactStatus.Implemented,
                [ProgramKitIdentifier.Parse("pkid:test:program-kit:unit-tests")]),
            new ArtifactCompatibility(
                ProgramKitIdentifier.Parse("pkid:contract:program-kit:compatibility-policy"),
                [
                    new CompatibilityClaim(
                        CompatibilityDimension.WireRead,
                        CompatibilityClassification.CompatibleAdditive,
                        []),
                ],
                exactVersion,
                exactVersion,
                []),
            new ArtifactProvenance(
                [
                    TestContractValues.Reference(
                        "pkid:design:program-kit:test-source"),
                ],
                ProgramKitIdentifier.Parse("pkid:project:program-kit:unit-tests"),
                "unit-test-correlation"),
            new ArtifactRepresentation(
                TestContractValues.Profile(
                    "pkid:profile:program-kit:json-contracts"),
                TestContractValues.Profile(
                    "pkid:profile:program-kit:canonical-json-rfc8785"),
                "application/json"),
            new ArtifactIntegrity("sha256", TestContractValues.Digest),
            "typed-document");
    }
}
