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
        "design-csharp-build-gate",
        "design-software",
        "develop-software",
        "implement-software-plan",
    ];

    private static readonly string[] RegisteredCapabilityIds =
    [
        "design-csharp-build-gate",
        "design-software",
        "develop-software",
        "implement-software-plan",
        "publish-dotnet-application-locally",
    ];

    private static readonly string[] RegisteredProviders =
    [
        "claude",
        "codex",
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
    public void AdapterTemplatesAreThinExactCanonicalPointerTemplates()
    {
        foreach (var provider in RegisteredProviders)
        {
            foreach (var capabilityId in RegisteredCapabilityIds)
            {
                var label = string.Concat(provider, "/", capabilityId);
                var wrapper = ConformanceInputs.Read(
                    string.Concat(
                        "Capabilities/Wrappers/",
                        provider,
                        "/",
                        capabilityId,
                        "/SKILL.md"));
                Assert.Contains(
                    string.Concat("name: ", capabilityId),
                    wrapper,
                    label);
                Assert.HasCount(
                    1,
                    wrapper.Split(
                        "{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}",
                        StringSplitOptions.None).Skip(1),
                    label);
                Assert.DoesNotContain("## Procedure", wrapper, label);
                Assert.DoesNotContain("## Allowed actions", wrapper, label);
                Assert.DoesNotContain("## Prohibited actions", wrapper, label);
                Assert.IsLessThan(4096, wrapper.Length, label);
            }
        }
    }

    [TestMethod]
    public void GateDesignFlowPreservesHumanAuthorityAndEstablishmentFirstExecution()
    {
        var design = ConformanceInputs.Read(
            "Capabilities/design-software/CAPABILITY.md");
        var gateDesign = ConformanceInputs.Read(
            "Capabilities/design-csharp-build-gate/CAPABILITY.md");
        var implementation = ConformanceInputs.Read(
            "Capabilities/implement-software-plan/CAPABILITY.md");

        Assert.Contains(
            "mandatory static-conformance disposition question",
            design);
        Assert.Contains(
            "Should we design one?",
            design);
        Assert.Contains(
            "A yes is an explicit",
            design);
        Assert.Contains(
            "missing wrapper is a setup blocker",
            design);
        Assert.Contains(
            "Use it only after a human explicitly starts",
            gateDesign);
        Assert.Contains(
            "Do not silently continue from `design-software`",
            gateDesign);
        Assert.Contains(
            "Do not accept an empty analyzer selection",
            gateDesign);
        Assert.Contains(
            "consumer-owned analyzer",
            gateDesign);
        Assert.IsFalse(
            gateDesign.Contains(
                string.Concat("domain", " analyzer"),
                StringComparison.OrdinalIgnoreCase));
        Assert.Contains(
            "dependency-ready `gate-establishment` units",
            implementation);
        Assert.Contains(
            "Do not run Program Kit's private `Orbyss.ProgramKit.CSharpGate`",
            implementation);
        Assert.Contains(
            "do not renew a temporary exception",
            implementation);
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
    public void BundleManifestAllowsExactlyFourDefinitionsAndTheirAdapters()
    {
        CapabilityBundleManifestReader reader = new();
        var manifest = reader.Read(
            ConformanceInputs.ReadBytes(
                "Capabilities/capability-bundle-manifest.json"));
        var capabilityIds = manifest.Capabilities
            .Select(entry => entry.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        Assert.AreSequenceEqual(DistributedCapabilityIds, capabilityIds);
        Assert.DoesNotContain(
            "publish-dotnet-application-locally",
            capabilityIds);
        Assert.DoesNotContain(
            "author-and-maintain-skills",
            capabilityIds);
        foreach (var provider in RegisteredProviders)
        {
            var adapterIds = manifest.OptionalProviderAdapters
                .Where(
                    entry => string.Equals(
                        entry.Provider,
                        provider,
                        StringComparison.Ordinal))
                .Select(entry => entry.CapabilityId)
                .Order(StringComparer.Ordinal)
                .ToArray();
            Assert.AreSequenceEqual(DistributedCapabilityIds, adapterIds);
        }

        Assert.HasCount(
            RegisteredProviders.Length * DistributedCapabilityIds.Length,
            manifest.OptionalProviderAdapters);
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
            Assert.Contains(adapter.Provider, RegisteredProviders);
            Assert.AreEqual(
                adapter.Sha256,
                Digest(
                    ConformanceInputs.ReadBytes(
                        string.Concat(
                            "Capabilities/Wrappers/",
                            adapter.Provider,
                            "/",
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
            13,
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
