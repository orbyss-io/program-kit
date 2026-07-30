namespace Orbyss.ProgramKit.UnitTests.Artifacts.Primitives;

[TestClass]
public sealed class ProgramKitIdentifierTests
{
    [TestMethod]
    [DataRow("pkid:package:program-kit:command-line")]
    [DataRow("pkid:approval-record:jtest:jtest-2.0")]
    [DataRow("pkid:schema:program-kit:planning.definitions.alpha-4")]
    public void CanonicalGrammarAcceptsExactFourSegmentIdentifiers(string value)
    {
        Assert.IsTrue(ProgramKitIdentifier.TryParse(value, out var identifier));
        Assert.AreEqual(value, identifier.Value);
    }

    [TestMethod]
    [DataRow("pkid:Package:program-kit:command-line")]
    [DataRow("pkid:package:program_kit:command-line")]
    [DataRow("pkid:package:program-kit:command..line")]
    [DataRow("pkid:package:program-kit:command-line.")]
    [DataRow("pkid:package:program-kit:-command")]
    [DataRow("pkid:package:program-kit:command--line")]
    [DataRow("pkid:package:program-kit")]
    [DataRow("pkid:package:program-kit:command:line")]
    public void CanonicalGrammarRejectsDivergentPunctuation(string value)
    {
        Assert.IsFalse(ProgramKitIdentifier.TryParse(value, out _));
        var validation = ProgramKitIdentifier.Validate(value, "/identity");
        Assert.IsFalse(validation.IsValid);
        Assert.AreEqual("/identity", validation.Diagnostics.Single().Path);
        Assert.Contains(
            ProgramKitIdentifier.CanonicalPattern,
            validation.Diagnostics.Single().Message);
    }
}
