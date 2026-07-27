using System.Text;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Catalog;

[TestClass]
public sealed class CapabilityIndexParserTests
{
    [TestMethod]
    public void ParsesAvailableAndUnavailableRowsWithoutChangingStatusMeaning()
    {
        CapabilityIndexParser sut = new();

        var result = sut.Parse(
            Encoding.UTF8.GetBytes(
                """
                # Capability index

                | Capability ID | Flow category | Status | Canonical definition | Active-provider wrapper | Notes |
                | --- | --- | --- | --- | --- | --- |
                | `design-software` | design | available | [CAPABILITY.md](design-software/CAPABILITY.md) | [Codex wrapper](../../.codex/skills/design-software/SKILL.md) | Design flow. |
                | `release-software` | release | unavailable | Not created | Not registered | Reserved flow. |
                """));

        Assert.HasCount(2, result.Entries);
        Assert.AreEqual("available", result.Entries[0].Status);
        Assert.AreEqual(
            "design-software/CAPABILITY.md",
            result.Entries[0].CanonicalDefinition);
        Assert.AreEqual("unavailable", result.Entries[1].Status);
        Assert.IsNull(result.Entries[1].CanonicalDefinition);
        Assert.IsNull(result.Entries[1].ActiveProviderWrapper);
    }

    [TestMethod]
    public void RejectsAnAvailableRowWithoutAnActiveWrapper()
    {
        CapabilityIndexParser sut = new();

        var exception = Assert.ThrowsExactly<CapabilityOperationException>(
            () => sut.Parse(
                Encoding.UTF8.GetBytes(
                    """
                    | Capability ID | Flow category | Status | Canonical definition | Active-provider wrapper | Notes |
                    | --- | --- | --- | --- | --- | --- |
                    | `design-software` | design | available | [CAPABILITY.md](design-software/CAPABILITY.md) | Not registered | Invalid. |
                    """)));

        Assert.AreEqual(CommandExitCode.UsageOrInputFailure, exception.ExitCode);
        Assert.AreEqual("PKCLI006", exception.DiagnosticId);
    }

    [TestMethod]
    public void RejectsDuplicateCapabilityIdentity()
    {
        CapabilityIndexParser sut = new();
        var content = Encoding.UTF8.GetBytes(
            """
            | Capability ID | Flow category | Status | Canonical definition | Active-provider wrapper | Notes |
            | --- | --- | --- | --- | --- | --- |
            | `design-software` | design | unavailable | Not created | Not registered | First. |
            | `design-software` | design | unavailable | Not created | Not registered | Duplicate. |
            """);

        var exception = Assert.ThrowsExactly<CapabilityOperationException>(
            () => sut.Parse(content));

        Assert.Contains("more than once", exception.Message);
    }
}
