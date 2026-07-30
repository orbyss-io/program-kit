using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
[TestCategory("ProgramKitGateExhaustive")]
public sealed class ReleaseBindingGateEstablishmentTests
{
    [TestMethod]
    public void ControlledBrokenFixturesFailClosed()
    {
        using var document = ReadFixture("broken-release-bindings.json");
        var fixtures = document.RootElement.EnumerateArray().ToArray();

        Assert.HasCount(7, fixtures);
        foreach (var fixture in fixtures)
        {
            Assert.AreEqual(
                fixture.GetProperty("expectedViolation").GetString(),
                ReleaseBindingFixtureValidator.FindViolation(fixture),
                fixture.GetProperty("caseId").GetString());
        }
    }

    [TestMethod]
    public void CompleteCanonicalBindingIsAccepted()
    {
        using var document = ReadFixture("valid-release-binding.json");

        Assert.IsNull(
            ReleaseBindingFixtureValidator.FindViolation(document.RootElement));
    }

    [TestMethod]
    public void UnknownFixtureKindFailsClosed()
    {
        using var document = JsonDocument.Parse(
            """
            {
              "kind": "future-unregistered-check",
              "facts": {}
            }
            """);

        Assert.AreEqual(
            "known-release-binding-fixture-kind",
            ReleaseBindingFixtureValidator.FindViolation(document.RootElement));
    }

    private static JsonDocument ReadFixture(string fileName) =>
        JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "ReleaseBinding",
            fileName)));
}
