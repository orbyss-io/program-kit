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
}
