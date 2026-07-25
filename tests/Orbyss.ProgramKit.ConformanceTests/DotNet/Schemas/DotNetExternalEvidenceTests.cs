using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Schemas;

[TestClass]
public sealed class DotNetExternalEvidenceTests
{
    [TestMethod]
    public void VendoredOpenApiSchemaMatchesFrozenOfficialBytes()
    {
        DotNetSchemaModule module = new(new OperationsSchemaModule());
        var resource = module.Resources.Single(static item =>
            item.ResourceName == "openapi-3.2.0-2025-11-23.schema.json");
        using var stream = module.OpenRead(resource.SchemaReference);
        var actual = string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant());

        Assert.AreEqual(
            "sha256:7d48f01f37eeae4799041b371ad5f533f9f533fd2b0caa1011a8ba27c5b48b70",
            actual);
        Assert.AreEqual(
            "https://spec.openapis.org/oas/3.2/schema/2025-11-23",
            resource.CanonicalUri.AbsoluteUri);
    }

    [TestMethod]
    public void CshellsEvidenceBindsAllFourAcceptedPackagesAndDirectContracts()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(static name =>
            name.EndsWith("cshells-0.0.28.json", StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resourceName)!;
        using var document = JsonDocument.Parse(stream);
        var root = document.RootElement;
        var text = root.GetRawText();

        Assert.AreEqual("0.0.28", root.GetProperty("packageVersion").GetString());
        Assert.HasCount(4, root.GetProperty("packages").EnumerateArray().ToArray());
        Assert.Contains(
            "IShellFeature.ConfigureServices",
            text);
        Assert.Contains(
            "IWebShellFeature.MapEndpoints",
            text);
        Assert.Contains(
            "29fe542835696131278fcacc6cdb9a6186fc0447",
            text);
    }

    [TestMethod]
    public void OpenTelemetryEvidenceBindsExactSpecificationsAndRestoredPackageBytes()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(static name =>
            name.EndsWith(
                "dotnet-telemetry-selection-1.0.0.json",
                StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resourceName)!;
        using var document = JsonDocument.Parse(stream);
        var root = document.RootElement;
        var selection = root.GetProperty("selection");
        var conventions = selection.GetProperty("semanticConventions");

        Assert.AreEqual(
            "1.55.0",
            selection
                .GetProperty("openTelemetrySpecification")
                .GetProperty("version")
                .GetString());
        Assert.AreEqual(
            "1.41.1",
            conventions.GetProperty("reviewedRevision").GetString());
        Assert.AreEqual(
            "1.23.0",
            conventions.GetProperty("httpEmissionRevision").GetString());
        Assert.IsEmpty(
            conventions.GetProperty("stabilityOptIns").EnumerateArray());
        Assert.AreEqual(
            "1.17.0",
            selection
                .GetProperty("openTelemetryDotNet")
                .GetProperty("version")
                .GetString());

        var packageRoot = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            ".nuget",
            "packages");
        foreach (var package in root.GetProperty("directPackages").EnumerateArray())
        {
            var packageId = package.GetProperty("id").GetString()!;
            var version = package.GetProperty("version").GetString()!;
            var archivePath = Path.Combine(
                packageRoot,
                packageId.ToLowerInvariant(),
                version,
                string.Concat(
                    packageId.ToLowerInvariant(),
                    ".",
                    version,
                    ".nupkg"));
            var actual = Convert.ToHexString(
                    SHA256.HashData(File.ReadAllBytes(archivePath)))
                .ToLowerInvariant();

            Assert.AreEqual(
                package.GetProperty("sha256").GetString(),
                actual,
                packageId);
        }
    }

    [TestMethod]
    public void TransportFailureEvidenceBindsExactFrameworkOnlyBehavior()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(static name =>
            name.EndsWith(
                "dotnet-transport-failure-selection-1.0.0.json",
                StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resourceName)!;
        using MemoryStream bytes = new();
        stream.CopyTo(bytes);
        Assert.AreEqual(
            "91f6f01a88f40bbbf21ee68b690f07c1a8d02a62aab3803b7b4442f8224b6218",
            Convert.ToHexString(SHA256.HashData(bytes.ToArray())).ToLowerInvariant());
        bytes.Position = 0;
        using var document = JsonDocument.Parse(bytes);
        var root = document.RootElement;
        var selection = root.GetProperty("selection");

        Assert.AreEqual("net10.0", selection.GetProperty("targetFramework").GetString());
        Assert.AreEqual(
            "Microsoft.AspNetCore.App",
            selection.GetProperty("runtimeSurface").GetString());
        Assert.IsEmpty(selection.GetProperty("externalPackages").EnumerateArray());
        Assert.HasCount(
            7,
            selection.GetProperty("frameworkApis").EnumerateArray().ToArray());
        Assert.AreEqual(
            "leave unhandled; never rewrite",
            root.GetProperty("policies")
                .GetProperty("responseStarted")
                .GetString());
        Assert.AreEqual(
            "fixed reviewed contract text; never Exception.Message",
            root.GetProperty("policies")
                .GetProperty("developmentDisclosure")
                .GetString());
    }
}
