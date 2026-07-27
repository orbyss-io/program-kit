using System.Collections.Immutable;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Catalog;

[TestClass]
public sealed class CapabilityCatalogRendererTests
{
    [TestMethod]
    public void RendersExactNonAuthoritativeCatalogWithSourceDigest()
    {
        CapabilityIndexDocument document = new(
            ImmutableArray.Create(
                new CapabilityIndexEntry(
                    "design-software",
                    "design",
                    "available",
                    "design-software/CAPABILITY.md",
                    "../provider-adapters/codex/design-software/SKILL.md",
                    "Design flow."),
                new CapabilityIndexEntry(
                    "release-software",
                    "release",
                    "unavailable",
                    null,
                    null,
                    "Reserved flow.")));

        var result = CapabilityCatalogRenderer.Render(
            document,
            "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");

        Assert.AreEqual(
            """
            # Capability catalog

            This file is a generated, non-authoritative projection of [`INDEX.md`](INDEX.md).
            Capability availability is owned only by the canonical index.

            Source path: `.agent-capabilities/capabilities/INDEX.md`
            Source digest: `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`

            | Capability ID | Flow category | Status | Canonical definition | Active-provider wrapper | Notes |
            | --- | --- | --- | --- | --- | --- |
            | `design-software` | design | available | [CAPABILITY.md](design-software/CAPABILITY.md) | [Codex adapter template](../provider-adapters/codex/design-software/SKILL.md) | Design flow. |
            | `release-software` | release | unavailable | Not created | Not registered | Reserved flow. |

            """.Replace("\r\n", "\n", StringComparison.Ordinal),
            Encoding.UTF8.GetString(result.Span));
    }
}
