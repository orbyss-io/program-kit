using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class SemanticVersionRegressionTests
{
    [TestMethod]
    public void ArbitrarilyLargeNumericCoreIdentifiersParseAndCompareByMagnitude()
    {
        var smaller = SemanticVersion.Parse(
            "999999999999999999999999999999.0.0");
        var larger = SemanticVersion.Parse(
            "1000000000000000000000000000000.0.0");

        Assert.IsTrue(smaller < larger);
        Assert.IsTrue(larger > smaller);
    }

    [TestMethod]
    public void ArbitrarilyLargeNumericPrereleaseIdentifiersCompareByMagnitude()
    {
        var smaller = SemanticVersion.Parse(
            "1.0.0-999999999999999999999999999999");
        var larger = SemanticVersion.Parse(
            "1.0.0-1000000000000000000000000000000");

        Assert.IsTrue(smaller < larger);
        Assert.IsTrue(larger > smaller);
    }

    [TestMethod]
    public void NumericPrereleaseIdentifierRemainsLowerThanNonnumericIdentifier()
    {
        var numeric = SemanticVersion.Parse(
            "1.0.0-999999999999999999999999999999");
        var nonnumeric = SemanticVersion.Parse("1.0.0-alpha");

        Assert.IsTrue(numeric < nonnumeric);
    }
}
