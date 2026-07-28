using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using Json.Schema;
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
        "maintain-software",
    ];

    private static readonly string[] RegisteredCapabilityIds =
    [
        "author-and-maintain-skills",
        "design-csharp-build-gate",
        "design-software",
        "develop-software",
        "implement-software-plan",
        "maintain-software",
        "publish-dotnet-application-locally",
    ];

    private static readonly string[] RegisteredProviders =
    [
        "claude",
        "codex",
    ];
    private static readonly string[] ExpectedCompletionConsumers =
    [
        "implement-software-plan",
        "maintain-software",
    ];
    private static readonly int[] ExpectedCompletionProfileOrder =
    [
        10,
        20,
        30,
        40,
        50,
        60,
        70,
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
    public void MaintenanceFlowIsBoundedSharedAndExactlyHumanUpgraded()
    {
        var routing = ConformanceInputs.Read(
            "Capabilities/develop-software/CAPABILITY.md");
        var maintenance = ConformanceInputs.Read(
            "Capabilities/maintain-software/CAPABILITY.md");

        Assert.Contains(
            "one small architecture-compatible change -> `maintain-software`",
            routing);
        Assert.Contains(
            "materially changed architecture",
            routing);
        Assert.Contains(
            "../../supporting-resources/completion-profiles/software-change/" +
            "completion-profile-set-1.0.0.json",
            maintenance);
        Assert.Contains(
            "exact human-approved Program Kit version",
            maintenance);
        Assert.Contains(
            "Do not auto-upgrade Program Kit",
            maintenance);
        Assert.Contains(
            "mapping is unambiguous",
            maintenance);
        Assert.Contains(
            "route to `design-software`",
            maintenance);
        Assert.Contains(
            "one reversible",
            maintenance);
    }

    [TestMethod]
    public void ProductCapabilityStandardIsDistributableAndAuthoringInert()
    {
        var authoring = ConformanceInputs.Read(
            "Capabilities/author-and-maintain-skills/CAPABILITY.md");
        Assert.Contains(
            "## Product capability distribution standard",
            authoring);
        Assert.Contains(
            "Every new or updated Program Kit product capability",
            authoring);
        Assert.Contains(
            "user-home global provider roots",
            authoring);
        Assert.Contains(
            "authoring, build, pack, and fixture verification remain inert",
            authoring);

        using var marker = JsonDocument.Parse(
            ConformanceInputs.ReadBytes(
                "Capabilities/authoring-workspace.json"));
        Assert.AreEqual(
            "denied",
            marker.RootElement
                .GetProperty("capabilityInitialization")
                .GetString());
        Assert.IsFalse(
            Directory.Exists(
                Path.Combine(
                    ConformanceInputs.ProgramKitRoot,
                    ".codex")));
        Assert.IsFalse(
            Directory.Exists(
                Path.Combine(
                    ConformanceInputs.ProgramKitRoot,
                    ".claude")));
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
    public void BundleManifestAllowsExactlyFiveDefinitionsAndTheirAdapters()
    {
        var schema = JsonSchema.FromText(
            ConformanceInputs.Read(
                "Schemas/capabilities/capability-bundle-manifest-0.1.0-alpha.1.schema.json"));
        using var document = JsonDocument.Parse(
            ConformanceInputs.ReadBytes(
                "Capabilities/capability-bundle-manifest.json"));
        var evaluation = schema.Evaluate(
            document.RootElement,
            new EvaluationOptions
            {
                OutputFormat = OutputFormat.List,
            });
        Assert.IsTrue(evaluation.IsValid);

        CapabilityBundleManifestReader reader = new();
        var manifest = reader.Read(
            ConformanceInputs.ReadBytes(
                "Capabilities/capability-bundle-manifest.json"));
        Assert.AreEqual("0.1.0-alpha.1", manifest.ManifestVersion);
        Assert.AreEqual("0.1.0-alpha.2", manifest.BundleVersion);
        Assert.AreEqual("0.1.0-alpha.2", manifest.KitVersion);
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

        Assert.HasCount(9, manifest.SupportingResources);
        foreach (var resource in manifest.SupportingResources)
        {
            const string sourcePrefix =
                ".agent-capabilities/supporting-resources/";
            Assert.StartsWith(sourcePrefix, resource.SourcePath);
            Assert.AreEqual(
                string.Concat(
                    "contentFiles/any/any/",
                    resource.SourcePath),
                resource.PackagePath);
            Assert.AreEqual(
                resource.Sha256,
                Digest(
                    ConformanceInputs.ReadBytes(
                        string.Concat(
                            "Capabilities/SupportingResources/",
                            resource.SourcePath[sourcePrefix.Length..]))));
        }
    }

    [TestMethod]
    public void SharedCompletionProfilesAreInertExactAndCommon()
    {
        const string root =
            "Capabilities/SupportingResources/completion-profiles/software-change/";
        var schema = JsonSchema.FromText(
            ConformanceInputs.Read(
                string.Concat(
                    root,
                    "completion-profile-set-1.0.0.schema.json")));
        using var document = JsonDocument.Parse(
            ConformanceInputs.ReadBytes(
                string.Concat(
                    root,
                    "completion-profile-set-1.0.0.json")));
        var evaluation = schema.Evaluate(
            document.RootElement,
            new EvaluationOptions
            {
                OutputFormat = OutputFormat.List,
            });
        Assert.IsTrue(evaluation.IsValid);

        var manifest = document.RootElement;
        Assert.AreEqual(
            "none",
            manifest.GetProperty("authority").GetString());
        Assert.IsFalse(
            manifest.GetProperty("independentlyInvokable").GetBoolean());
        var consumers = manifest
            .GetProperty("consumers")
            .EnumerateArray()
            .ToArray();
        Assert.AreSequenceEqual(
            ExpectedCompletionConsumers,
            consumers
                .Select(
                    consumer =>
                        consumer.GetProperty("capabilityId").GetString())
                .ToArray());
        var implementationProfiles = consumers[0]
            .GetProperty("profileIds")
            .EnumerateArray()
            .Select(static item => item.GetString())
            .ToArray();
        var maintenanceProfiles = consumers[1]
            .GetProperty("profileIds")
            .EnumerateArray()
            .Select(static item => item.GetString())
            .ToArray();
        Assert.AreSequenceEqual(
            implementationProfiles,
            maintenanceProfiles);

        var profiles = manifest
            .GetProperty("profiles")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(7, profiles);
        Assert.AreSequenceEqual(
            ExpectedCompletionProfileOrder,
            profiles
                .Select(profile => profile.GetProperty("order").GetInt32())
                .ToArray());
        foreach (var profile in profiles)
        {
            var relativePath = profile.GetProperty("path").GetString() ??
                throw new AssertFailedException("Missing profile path.");
            var bytes = ConformanceInputs.ReadBytes(
                string.Concat(root, relativePath));
            Assert.AreEqual(
                profile.GetProperty("sha256").GetString(),
                Digest(bytes));
            var text = Encoding.UTF8.GetString(bytes);
            Assert.StartsWith("# ", text);
            Assert.DoesNotStartWith("---", text);
            Assert.Contains(
                "not a capability,",
                text,
                relativePath);
            Assert.Contains(
                "not",
                text,
                relativePath);
        }

        var implementation = ConformanceInputs.Read(
            "Capabilities/implement-software-plan/CAPABILITY.md");
        Assert.Contains(
            "../../supporting-resources/completion-profiles/software-change/" +
            "completion-profile-set-1.0.0.json",
            implementation);
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
            25,
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
