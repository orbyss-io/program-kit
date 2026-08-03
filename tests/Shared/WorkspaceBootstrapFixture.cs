using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Distribution;
using Orbyss.ProgramKit.Providers.DotNet.Manifests;

namespace Orbyss.ProgramKit.Tests;

internal static class WorkspaceBootstrapFixture
{
    private const string Digest = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    public static JsonObject DistributionBinding() => new()
    {
        ["schema"] = "program-kit.distribution-binding/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,
        ["packageId"] = DistributionDescriptor.PackageId,
        ["packageVersion"] = DistributionDescriptor.Version,
        ["commandName"] = DistributionDescriptor.CommandName,
        ["invocationKind"] = "dotnet-tool-manifest",
        ["toolManifest"] = ".config/dotnet-tools.json",
        ["reportedVersion"] = DistributionDescriptor.Version,
        ["packageDigest"] = Digest,
        ["executableDigest"] = Digest,
        ["runtimeProfile"] = Identity("orbyss.program-kit", "runtime-profile", "net10.0"),
        ["distribution"] = Identity("orbyss.program-kit", "distribution", "program-kit-cli"),
    };

    public static JsonObject WorkspaceIdentity(string name = "consumer-workspace") => Identity("consumer.example", "workspace", name);

    public static JsonObject InitRequest() => new()
    {
        ["schema"] = "program-kit.workspace-init-request/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,
        ["workspaceIdentity"] = WorkspaceIdentity(),
        ["distributionBinding"] = DistributionBinding(),
        ["requestedBy"] = "human-reviewer",
        ["requestedEffect"] = "bootstrap-absent-files",
        ["manifestPath"] = "program-kit.yaml",
        ["lockPath"] = "program-kit.lock.json",
    };

    public static JsonObject CatalogRequest() => new()
    {
        ["schema"] = "program-kit.catalog-request/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,
        ["scope"] = "distribution",
        ["distributionBinding"] = DistributionBinding(),
    };

    public static JsonObject RestoreRequest(string mode) => new()
    {
        ["schema"] = "program-kit.workspace-restore-request/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,
        ["workspaceIdentity"] = WorkspaceIdentity(),
        ["distributionBinding"] = DistributionBinding(),
        ["manifest"] = "program-kit.yaml",
        ["lockPath"] = "program-kit.lock.json",
        ["mode"] = mode,
        ["allowedSources"] = new JsonArray(),
    };

    public static JsonObject ExactFactoryManifest(bool duplicateAlias = false)
    {
        ProviderManifest provider = DotNetProviderManifest.Create();
        GovernedIdentity profile = DistributionCatalogService.Profile(new ProviderStub(provider), DotNetProviderManifest.Profile);
        JsonObject selection = new()
        {
            ["alias"] = "dotnet-default",
            ["provider"] = ContractJson.Identity(provider.Identity),
            ["targetProfile"] = ContractJson.Identity(profile),
            ["selectionAuthority"] = Identity("consumer.example", "selection-authority", "human-review"),
        };
        JsonArray selections = new(selection);
        if (duplicateAlias) selections.Add(selection.DeepClone());
        return new JsonObject
        {
            ["schema"] = "program-kit.workspace/v1",
            ["distribution"] = DistributionBinding(),
            ["factory"] = new JsonObject { ["selections"] = selections, ["defaultSelection"] = "dotnet-default" },
        };
    }

    public static string WriteRequest(string workspace, string name, JsonObject request)
    {
        string directory = Path.Combine(workspace, "requests");
        Directory.CreateDirectory(directory);
        string path = Path.Combine(directory, name);
        File.WriteAllBytes(path, CanonicalJson.Encode(request));
        return path;
    }

    private static JsonObject Identity(string authority, string kind, string name) => new()
    {
        ["authority"] = authority,
        ["kind"] = kind,
        ["name"] = name,
        ["revision"] = "1.0.0",
        ["digest"] = Digest,
    };

    private sealed class ProviderStub : IFactoryProvider
    {
        public ProviderStub(ProviderManifest manifest) { Manifest = manifest; }
        public ProviderManifest Manifest { get; }
    }
}
