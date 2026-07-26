using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Schemas;

[TestClass]
public sealed class DotNetExternalEvidenceTests
{
    private static readonly string[] OAuthStandards =
        ["RFC 6749", "RFC 8693", "RFC 8707"];

    [TestMethod]
    public void VendoredOpenApiSchemaMatchesFrozenOfficialBytes()
    {
        DotNetSchemaModule module = new(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
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

    [TestMethod]
    public void SecurityEvidenceBindsExactProtocolProfilesAndPackageArchives()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(
            static name => name.EndsWith(
                "dotnet-security-selection-1.0.0.json",
                StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resourceName)!;
        using MemoryStream bytes = new();
        stream.CopyTo(bytes);
        Assert.AreEqual(
            "71760d93aa57802ba9524a04c93e5bfa59ed0cab1c5f3a3902de2215f9c41f9c",
            Convert.ToHexString(SHA256.HashData(bytes.ToArray()))
                .ToLowerInvariant());
        bytes.Position = 0;
        using var document = JsonDocument.Parse(bytes);
        var root = document.RootElement;
        var packages = root.GetProperty("directPackages")
            .EnumerateArray()
            .ToArray();

        Assert.HasCount(2, packages);
        Assert.AreEqual(
            "excluded",
            root.GetProperty("selection")
                .GetProperty("domainAuthorizationMeaning")
                .GetString());
        Assert.AreEqual(
            "classified secret reference or assertion-service reference only; no secret value in shell, source, evidence, or logs",
            root.GetProperty("policies")
                .GetProperty("clientMaterial")
                .GetString());

        var packageRoot = Environment.GetEnvironmentVariable(
                "NUGET_PACKAGES") ??
            Path.Combine(
                Environment.GetFolderPath(
                    Environment.SpecialFolder.UserProfile),
                ".nuget",
                "packages");
        foreach (var package in packages)
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
    public void PublicBrowserEvidenceBindsExactAdapterPackagesAndAssemblies()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(
            static name => name.EndsWith(
                "dotnet-public-browser-selection-1.0.0.json",
                StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resourceName)!;
        using MemoryStream bytes = new();
        stream.CopyTo(bytes);
        Assert.AreEqual(
            "ab9fe10529b7087c75d24e0e0f3267c7adc1dd0832120d0a7a5b868b228f0ef4",
            Convert.ToHexString(SHA256.HashData(bytes.ToArray()))
                .ToLowerInvariant());
        bytes.Position = 0;
        using var document = JsonDocument.Parse(bytes);
        var root = document.RootElement;
        var packages = root.GetProperty("directPackages")
            .EnumerateArray()
            .ToArray();

        Assert.HasCount(3, packages);
        Assert.IsTrue(
            root.GetProperty("selection")
                .GetProperty("humanThreatAcceptanceRequired")
                .GetBoolean());
        Assert.AreEqual(
            "absent",
            root.GetProperty("selection")
                .GetProperty("refreshDisposition")
                .GetString());
        var generatorPath = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "src",
            "Orbyss.ProgramKit.DotNet",
            "Generation",
            "DotNetSecurityProjectionCompiler.cs");
        Assert.AreEqual(
            Orbyss.ProgramKit.DotNet.Operations.Security
                .DotNetPublicBrowserTargetAdapterCatalog
                .BlazorWebAssemblyOidc
                .GeneratorRevision
                .Digest
                .Value,
            string.Concat(
                "sha256:",
                Convert.ToHexString(
                        SHA256.HashData(File.ReadAllBytes(generatorPath)))
                    .ToLowerInvariant()));

        var packageRoot = Environment.GetEnvironmentVariable(
                "NUGET_PACKAGES") ??
            Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                ".nuget",
                "packages");
        foreach (var package in packages)
        {
            var packageId = package.GetProperty("id").GetString()!;
            var version = package.GetProperty("version").GetString()!;
            var packageDirectory = Path.Combine(
                packageRoot,
                packageId.ToLowerInvariant(),
                version);
            var archivePath = Path.Combine(
                packageDirectory,
                string.Concat(packageId.ToLowerInvariant(), ".", version, ".nupkg"));
            Assert.AreEqual(
                package.GetProperty("sha256").GetString(),
                Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(archivePath)))
                    .ToLowerInvariant(),
                packageId);

            var targetFramework = packageId == "Microsoft.Playwright"
                ? "netstandard2.0"
                : "net10.0";
            var assemblyPath = Path.Combine(
                packageDirectory,
                "lib",
                targetFramework,
                string.Concat(packageId, ".dll"));
            Assert.AreEqual(
                package.GetProperty("assemblySha256").GetString(),
                Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(assemblyPath)))
                    .ToLowerInvariant(),
                packageId);
        }
    }

    [TestMethod]
    public void OAuthServiceClientEvidenceBindsExactStandardsAndFrameworkBoundary()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(
            static name => name.EndsWith(
                "dotnet-oauth-service-clients-selection-1.0.0.json",
                StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resourceName)!;
        using MemoryStream bytes = new();
        stream.CopyTo(bytes);
        Assert.AreEqual(
            "f7f89ccbcd3ed86164465a41e8926208699539ea39a8a77a06e025f6d4054525",
            Convert.ToHexString(SHA256.HashData(bytes.ToArray()))
                .ToLowerInvariant());
        bytes.Position = 0;
        using var document = JsonDocument.Parse(bytes);
        var root = document.RootElement;

        Assert.IsEmpty(root.GetProperty("directPackages").EnumerateArray());
        Assert.AreEqual(
            "Microsoft.AspNetCore.App@10.0.10",
            root.GetProperty("selection")
                .GetProperty("sharedFramework")
                .GetString());
        Assert.IsFalse(
            root.GetProperty("selection")
                .GetProperty("automaticRetry")
                .GetBoolean());
        Assert.IsFalse(
            root.GetProperty("selection")
                .GetProperty("ambientCurrentUserToken")
                .GetBoolean());
        var generatorPath = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "src",
            "Orbyss.ProgramKit.DotNet",
            "Generation",
            "DotNetOAuthServiceClientProjectionRenderer.cs");
        Assert.AreEqual(
            root.GetProperty("selection")
                .GetProperty("generatorSha256")
                .GetString(),
            Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(generatorPath)))
                .ToLowerInvariant());
        Assert.AreSequenceEqual(
            OAuthStandards,
            root.GetProperty("standards")
                .EnumerateArray()
                .Select(static item => item.GetProperty("revision").GetString())
                .ToArray());
    }

    [TestMethod]
    public void AzureKeyVaultEvidenceBindsExactPackageCompilerAndDeferral()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(
            static name => name.EndsWith(
                "dotnet-azure-configuration-selection-1.0.0.json",
                StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resourceName)!;
        using MemoryStream bytes = new();
        stream.CopyTo(bytes);
        Assert.AreEqual(
            "204949c63de6dbbea3740b29618f154d36947e4f2086d4d695abc0dd7a982495",
            Convert.ToHexString(SHA256.HashData(bytes.ToArray()))
                .ToLowerInvariant());
        bytes.Position = 0;
        using var document = JsonDocument.Parse(bytes);
        var root = document.RootElement;
        var package = root.GetProperty("availableAdapters")[0];
        var packageRoot = Environment.GetEnvironmentVariable(
                "NUGET_PACKAGES") ??
            Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                ".nuget",
                "packages");
        var packageDirectory = Path.Combine(
            packageRoot,
            package.GetProperty("package").GetString()!.ToLowerInvariant(),
            package.GetProperty("version").GetString()!);
        var archivePath = Path.Combine(
            packageDirectory,
            "azure.extensions.aspnetcore.configuration.secrets.1.5.1.nupkg");
        var assemblyPath = Path.Combine(
            packageDirectory,
            "lib",
            "net10.0",
            "Azure.Extensions.AspNetCore.Configuration.Secrets.dll");

        Assert.AreEqual(
            package.GetProperty("packageSha256").GetString(),
            Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(archivePath)))
                .ToLowerInvariant());
        Assert.AreEqual(
            package.GetProperty("net10AssemblySha256").GetString(),
            Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(assemblyPath)))
                .ToLowerInvariant());
        Assert.AreEqual(
            root.GetProperty("target")
                .GetProperty("generatorSha256")
                .GetString(),
            Convert.ToHexString(
                    SHA256.HashData(File.ReadAllBytes(Path.Combine(
                        ConformanceInputs.RepositoryRoot,
                        "program-kit",
                        "src",
                        "Orbyss.ProgramKit.DotNet",
                        "Generation",
                        "ConfigurationProviders",
                        "DotNetAzureConfigurationProviderGenerator.cs"))))
                .ToLowerInvariant());
        Assert.HasCount(
            2,
            root.GetProperty("deferredAdapters")[0]
                .GetProperty("reviewedPackages")
                .EnumerateArray()
                .ToArray());
        Assert.AreEqual(
            "not registered, generated, packaged, or advertised",
            root.GetProperty("deferredAdapters")[0]
                .GetProperty("availability")
                .GetString());
    }
}
