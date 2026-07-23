using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class ArtifactPrimitiveTests
{
    [TestMethod]
    public void ProgramKitIdentifierAcceptsOnlyTheCanonicalFourTokenGrammar()
    {
        var identifier = ProgramKitIdentifier.Parse(
            "pkid:contract:program-kit:artifact-envelope");

        Assert.AreEqual("contract", identifier.Kind);
        Assert.AreEqual("program-kit", identifier.Scope);
        Assert.AreEqual("artifact-envelope", identifier.Name);

        Assert.IsFalse(ProgramKitIdentifier.TryParse("PKID:contract:program-kit:name", out _));
        Assert.IsFalse(ProgramKitIdentifier.TryParse("pkid:contract:program-kit", out _));
        Assert.IsFalse(ProgramKitIdentifier.TryParse("pkid:contract:program--kit:name", out _));
        Assert.IsFalse(ProgramKitIdentifier.TryParse("pkid:contract:program_kit:name", out _));
    }

    [TestMethod]
    public void SemanticVersionUsesStrictSemVerPrecedence()
    {
        var alpha = SemanticVersion.Parse("1.0.0-alpha.1");
        var beta = SemanticVersion.Parse("1.0.0-beta.1");
        var stable = SemanticVersion.Parse("1.0.0");

        Assert.IsTrue(alpha < beta);
        Assert.IsTrue(beta < stable);
        Assert.IsTrue(stable >= alpha);
        Assert.IsFalse(SemanticVersion.TryParse("1.0", out _));
        Assert.IsFalse(SemanticVersion.TryParse("01.0.0", out _));
        Assert.IsFalse(SemanticVersion.TryParse("1.0.0-01", out _));
    }

    [TestMethod]
    public void SemanticVersionRangeSupportsExactAndBoundedSelections()
    {
        var exact = SemanticVersionRange.Parse("[0.1.0-alpha.1]");
        var bounded = SemanticVersionRange.Parse("[1.0.0,2.0.0)");

        Assert.IsTrue(exact.Contains(SemanticVersion.Parse("0.1.0-alpha.1")));
        Assert.IsFalse(exact.Contains(SemanticVersion.Parse("0.1.0-alpha.2")));
        Assert.IsTrue(bounded.Contains(SemanticVersion.Parse("1.9.9")));
        Assert.IsFalse(bounded.Contains(SemanticVersion.Parse("2.0.0")));
        Assert.IsFalse(SemanticVersionRange.TryParse("[,]", out _));
    }

    [TestMethod]
    public void Sha256DigestRequiresAlgorithmQualificationAndLowercaseHex()
    {
        var valid = $"sha256:{new string('a', 64)}";

        Assert.IsTrue(Sha256Digest.TryParse(valid, out var digest));
        Assert.AreEqual(valid, digest.Value);
        Assert.IsFalse(Sha256Digest.TryParse(new string('a', 64), out _));
        Assert.IsFalse(Sha256Digest.TryParse($"sha256:{new string('A', 64)}", out _));
    }

    [TestMethod]
    public void ProfileReferenceMustUseTheProfileIdentityKind()
    {
        var reference = new ProfileReference(
            ProgramKitIdentifier.Parse("pkid:profile:program-kit:test-profile"),
            SemanticVersion.Parse("1.0.0"),
            TestContractValues.Digest);
        var invalid = reference with
        {
            Identity = ProgramKitIdentifier.Parse("pkid:contract:program-kit:test-profile"),
        };

        Assert.IsTrue(new ProfileReferenceValidator().Validate(reference).IsValid);
        Assert.IsFalse(new ProfileReferenceValidator().Validate(invalid).IsValid);
    }
}
