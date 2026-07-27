namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Projections;

[TestClass]
public sealed class ProjectionFreshnessCheckerTests
{
    [TestMethod]
    public void CheckRejectsAChangedExactInputDigest()
    {
        ProjectionFreshnessChecker sut = new();
        var declared = TestContractValues.Reference(
            "pkid:artifact:program-kit:source");
        var current = declared with
        {
            Digest = Sha256Digest.Parse(string.Concat("sha256:", new string('b', 64))),
        };

        var result = sut.Check([new ProjectionBinding(declared, current)]);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.StaleProjection));
    }
}
