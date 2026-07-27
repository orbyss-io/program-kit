using System.Security.Cryptography;
using System.Text;
using System.Xml.Linq;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.ConformanceTests.Infrastructure;

namespace Orbyss.ProgramKit.ConformanceTests.Governance;

[TestClass]
public sealed class CapabilityDeliveryConformanceTests
{
    private static readonly string[] DistributedCapabilityIds =
    [
        "design-software",
        "develop-software",
        "implement-software-plan",
    ];

    private static readonly string[] RegisteredCapabilityIds =
    [
        "design-software",
        "develop-software",
        "implement-software-plan",
        "publish-dotnet-application-locally",
    ];

    [TestMethod]
    public void CanonicalDefinitionsCarryEveryRequiredCapabilityBoundary()
    {
        string[] requiredSections =
        [
            "## Identity and trigger",
            "## Purpose",
            "## Non-goals",
            "## Inputs and outputs",
            "## Preconditions",
            "## Allowed actions",
            "## Prohibited actions",
            "## Stop conditions",
            "## Source of truth and freshness",
            "## Procedure",
            "## Verification and failure reporting",
            "## Authority and safety boundaries",
            "## Compatibility and versioning",
            "## Provider wrapper mapping and drift check",
        ];

        foreach (var capabilityId in RegisteredCapabilityIds)
        {
            var definition = ConformanceInputs.Read(
                string.Concat(
                    "Capabilities/",
                    capabilityId,
                    "/CAPABILITY.md"));
            Assert.StartsWith(
                string.Concat("# ", capabilityId),
                definition,
                capabilityId);
            foreach (var section in requiredSections)
            {
                Assert.Contains(section, definition, capabilityId);
            }
        }
    }

    [TestMethod]
    public void CodexAdapterTemplatesAreThinExactCanonicalPointerTemplates()
    {
        foreach (var capabilityId in RegisteredCapabilityIds)
        {
            var wrapper = ConformanceInputs.Read(
                string.Concat(
                    "Capabilities/Wrappers/",
                    capabilityId,
                    "/SKILL.md"));
            Assert.Contains(
                string.Concat("name: ", capabilityId),
                wrapper,
                capabilityId);
            Assert.HasCount(
                1,
                wrapper.Split(
                    "{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}",
                    StringSplitOptions.None).Skip(1),
                capabilityId);
            Assert.DoesNotContain("## Procedure", wrapper, capabilityId);
            Assert.DoesNotContain("## Allowed actions", wrapper, capabilityId);
            Assert.DoesNotContain("## Prohibited actions", wrapper, capabilityId);
            Assert.IsLessThan(4096, wrapper.Length, capabilityId);
        }
    }

    [TestMethod]
    public void IndexAndGeneratedCatalogAgreeAtExactCurrentBytes()
    {
        var indexBytes = ConformanceInputs.ReadBytes(
            "Capabilities/INDEX.md");
        var expectedCatalog = ConformanceInputs.ReadBytes(
            "Capabilities/README.md");
        CapabilityIndexParser parser = new();
        var index = parser.Parse(indexBytes);
        var digest = Digest(indexBytes);

        var actualCatalog = CapabilityCatalogRenderer.Render(index, digest);

        Assert.AreSequenceEqual(expectedCatalog, actualCatalog.ToArray());
        foreach (var capabilityId in RegisteredCapabilityIds)
        {
            Assert.ContainsSingle(
                index.Entries.Where(
                    entry =>
                        string.Equals(
                            entry.CapabilityId,
                            capabilityId,
                            StringComparison.Ordinal) &&
                        string.Equals(
                            entry.Status,
                            "available",
                            StringComparison.Ordinal)));
        }

        foreach (var capabilityId in new[]
                 {
                     "release-software",
                     "qualify-release-candidate",
                     "promote-qualified-release",
                 })
        {
            Assert.ContainsSingle(
                index.Entries.Where(
                    entry =>
                        string.Equals(
                            entry.CapabilityId,
                            capabilityId,
                            StringComparison.Ordinal) &&
                        string.Equals(
                            entry.Status,
                            "unavailable",
                            StringComparison.Ordinal)));
        }
    }

    [TestMethod]
    public void BundleManifestAllowsExactlyThreeDefinitionsAndTheirAdapters()
    {
        CapabilityBundleManifestReader reader = new();
        var manifest = reader.Read(
            ConformanceInputs.ReadBytes(
                "Capabilities/capability-bundle-manifest.json"));
        var capabilityIds = manifest.Capabilities
            .Select(entry => entry.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var adapterIds = manifest.OptionalProviderAdapters
            .Select(entry => entry.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(DistributedCapabilityIds, capabilityIds);
        Assert.AreSequenceEqual(DistributedCapabilityIds, adapterIds);
        Assert.DoesNotContain(
            "publish-dotnet-application-locally",
            capabilityIds);
        Assert.DoesNotContain(
            "author-and-maintain-skills",
            capabilityIds);
        foreach (var capability in manifest.Capabilities)
        {
            Assert.AreEqual(
                capability.Sha256,
                Digest(
                    ConformanceInputs.ReadBytes(
                        string.Concat(
                            "Capabilities/",
                            capability.CapabilityId,
                            "/CAPABILITY.md"))));
        }

        foreach (var adapter in manifest.OptionalProviderAdapters)
        {
            Assert.AreEqual("codex", adapter.Provider);
            Assert.AreEqual(
                adapter.Sha256,
                Digest(
                    ConformanceInputs.ReadBytes(
                        string.Concat(
                            "Capabilities/Wrappers/",
                            adapter.CapabilityId,
                            "/SKILL.md"))));
        }
    }

    [TestMethod]
    public void CapabilityBundleProjectPacksNoAssemblyOrDependency()
    {
        var projectPath = ConformanceInputs.Files(
                "Projects",
                "Orbyss.ProgramKit.CapabilityBundle.csproj")
            .Single();
        var project = XDocument.Load(projectPath);

        Assert.AreEqual(
            "false",
            project.Descendants("IncludeBuildOutput").Single().Value);
        Assert.AreEqual(
            "false",
            project.Descendants("IncludeSymbols").Single().Value);
        Assert.AreEqual(
            "true",
            project.Descendants("SuppressDependenciesWhenPacking").Single().Value);
        Assert.IsEmpty(project.Descendants("ProjectReference"));
        Assert.IsEmpty(project.Descendants("PackageReference"));
        Assert.HasCount(
            7,
            project
                .Descendants("None")
                .Where(
                    item =>
                        RequiredAttribute(item, "PackagePath")
                            .StartsWith(
                                "contentFiles/any/any/.agent-capabilities/",
                                StringComparison.Ordinal)));
    }

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());

    private static string RequiredAttribute(XElement element, string name) =>
        element.Attribute(name)?.Value ??
        throw new AssertFailedException(
            $"Missing {name} on {element.Name}.");
}
