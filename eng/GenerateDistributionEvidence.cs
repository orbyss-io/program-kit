#:project ../src/ProgramKit.Kernel/ProgramKit.Kernel.csproj
#:project ../src/ProgramKit.Providers.DotNet/ProgramKit.Providers.DotNet.csproj
#:project ../src/ProgramKit.SessionIntegration/ProgramKit.SessionIntegration.csproj
#:project ../src/ProgramKit.SessionIntegration.Providers.Codex/ProgramKit.SessionIntegration.Providers.Codex.csproj
#:property PublishAot=false
#:property RestoreLockedMode=false
#:property NuGetAudit=false

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Providers.DotNet.Manifests;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;

string root = Directory.GetCurrentDirectory();
if (!File.Exists(Path.Combine(root, "global.json")))
{
    throw new InvalidOperationException("Run distribution evidence generation from the repository root.");
}

string output = Path.Combine(root, "artifacts", "evidence");
Directory.CreateDirectory(output);

string ByteDigest(string path) => $"sha256:{Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant()}";
byte[] CanonicalSourceBytes(string path)
{
    byte[] bytes = File.ReadAllBytes(path);
    string logicalPath = Path.GetRelativePath(root, path).Replace('\\', '/');
    if (bytes.AsSpan().StartsWith(Encoding.UTF8.Preamble))
    {
        throw new InvalidOperationException($"Source artifact '{logicalPath}' must use UTF-8 without a byte-order mark.");
    }

    if (bytes.AsSpan().Contains((byte)'\r'))
    {
        throw new InvalidOperationException($"Source artifact '{logicalPath}' must use canonical LF line endings.");
    }

    try
    {
        _ = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false, throwOnInvalidBytes: true).GetString(bytes);
    }
    catch (DecoderFallbackException exception)
    {
        throw new InvalidOperationException($"Source artifact '{logicalPath}' must contain valid UTF-8.", exception);
    }

    return bytes;
}
string SourceDigest(string path) => $"sha256:{Convert.ToHexString(SHA256.HashData(CanonicalSourceBytes(path))).ToLowerInvariant()}";
JsonObject Identity(GovernedIdentity identity) => new()
{
    ["authority"] = identity.Authority,
    ["kind"] = identity.Kind,
    ["name"] = identity.Name,
    ["revision"] = identity.Revision,
    ["digest"] = identity.Digest,
};
JsonArray Strings(IEnumerable<string> values) => new(values.OrderBy(static value => value, StringComparer.Ordinal).Select(static value => JsonValue.Create(value)).ToArray());
string Write(string name, JsonObject document)
{
    string path = Path.Combine(output, name);
    File.WriteAllBytes(path, CanonicalJson.Encode(document));
    return ByteDigest(path);
}

ProviderManifest provider = DotNetProviderManifest.Create();
JsonObject support = new()
{
    ["schema"] = "program-kit.provider-support/v1",
    ["canonicalProfile"] = CanonicalJson.Profile,
    ["provider"] = Identity(provider.Identity),
    ["distribution"] = Identity(provider.Distribution),
    ["roles"] = Strings(provider.Roles.Select(role => Kebab(role.ToString()))),
    ["profiles"] = Strings(provider.Profiles),
    ["inputKinds"] = Strings(provider.InputKinds),
    ["outputKinds"] = Strings(provider.OutputKinds),
    ["processes"] = Strings(provider.Processes),
    ["filesystemEffects"] = Strings(provider.FilesystemEffects),
};
string supportDigest = Write("provider-support.json", support);
if (!string.Equals(supportDigest, provider.ConformanceEvidence.Single().Artifact.Digest, StringComparison.Ordinal))
{
    throw new InvalidOperationException("Provider support evidence does not match its exact runtime manifest binding.");
}

JsonObject Catalog(string idPrefix)
{
    JsonArray entries = new(DiagnosticCatalog.Entries.Values
        .Where(definition => definition.Id.StartsWith(idPrefix, StringComparison.Ordinal))
        .OrderBy(static definition => definition.Id, StringComparer.Ordinal)
        .Select(definition => new JsonObject
        {
            ["id"] = definition.Id,
            ["trigger"] = definition.Observed,
            ["violatedInvariant"] = definition.Expected,
            ["category"] = Kebab(definition.Category.ToString()),
            ["defaultSeverity"] = Kebab(definition.Severity.ToString()),
            ["messageKey"] = definition.MessageKey,
            ["primaryDisposition"] = Kebab(definition.Disposition.ToString()),
            ["parameterDisclosure"] = new JsonObject(),
            ["remediationKinds"] = new JsonArray(Kebab(definition.Disposition.ToString())),
            ["status"] = "active",
        }).ToArray());
    return new JsonObject
    {
        ["schema"] = "program-kit.diagnostic-catalog/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,

        ["protocolRevision"] = "1.0.0",
        ["entries"] = entries,
    };
}

string kernelCatalogDigest = Write("kernel-diagnostic-catalog.json", Catalog("program-kit.kernel/"));
string providerCatalogDigest = Write("dotnet-diagnostic-catalog.json", Catalog("program-kit.provider.dotnet/"));
string sessionCatalogDigest = Write("session-diagnostic-catalog.json", SessionDiagnosticCatalog.ToDocument());
string codexCatalogDigest = Write("codex-diagnostic-catalog.json", CodexDiagnosticCatalog.ToDocument());
if (!string.Equals(kernelCatalogDigest, DiagnosticCatalogArtifacts.KernelArtifact.Digest, StringComparison.Ordinal)
    || !string.Equals(providerCatalogDigest, provider.DiagnosticCatalog.Digest, StringComparison.Ordinal)
    || !string.Equals(sessionCatalogDigest, SessionDiagnosticCatalog.Identity.Digest, StringComparison.Ordinal)
    || !string.Equals(codexCatalogDigest, CodexDiagnosticCatalog.Identity.Digest, StringComparison.Ordinal))
{
    throw new InvalidOperationException("A diagnostic catalog changed without an exact content-bound identity update.");
}

List<JsonObject> dependencies = new();
foreach (string lockPath in Directory.EnumerateFiles(root, "packages.lock.json", SearchOption.AllDirectories)
    .Where(static path => !path.Contains($"{Path.DirectorySeparatorChar}bin{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase)
        && !path.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase))
    .OrderBy(static path => path, StringComparer.Ordinal))
{
    JsonObject lockDocument = CanonicalJson.Parse(File.ReadAllBytes(lockPath)).AsObject();
    foreach (KeyValuePair<string, JsonNode?> framework in lockDocument["dependencies"]!.AsObject().OrderBy(static pair => pair.Key, StringComparer.Ordinal))
    {
        foreach (KeyValuePair<string, JsonNode?> dependency in framework.Value!.AsObject().OrderBy(static pair => pair.Key, StringComparer.OrdinalIgnoreCase))
        {
            JsonObject detail = dependency.Value!.AsObject();
            string type = detail["type"]!.GetValue<string>();
            if (type == "Project") continue;
            dependencies.Add(new JsonObject
            {
                ["name"] = dependency.Key,
                ["version"] = detail["resolved"]!.GetValue<string>(),
                ["type"] = type,
                ["contentHash"] = detail["contentHash"]!.GetValue<string>(),
                ["sourceLock"] = Path.GetRelativePath(root, lockPath).Replace('\\', '/'),
                ["framework"] = framework.Key,
            });
        }
    }
}
JsonArray components = new(dependencies
    .GroupBy(static item => $"{item["name"]!.GetValue<string>()}\n{item["version"]!.GetValue<string>()}\n{item["contentHash"]!.GetValue<string>()}", StringComparer.OrdinalIgnoreCase)
    .Select(static group => group.OrderBy(static item => item["sourceLock"]!.GetValue<string>(), StringComparer.Ordinal).First())
    .OrderBy(static item => item["name"]!.GetValue<string>(), StringComparer.OrdinalIgnoreCase)
    .ThenBy(static item => item["version"]!.GetValue<string>(), StringComparer.Ordinal)
    .Select(static item => item.DeepClone()).ToArray());
JsonObject sbom = new()
{
    ["bomFormat"] = "CycloneDX",
    ["specVersion"] = "1.6",
    ["serialNumber"] = "urn:uuid:00000000-0000-0000-0000-000000000001",
    ["version"] = 1,
    ["metadata"] = new JsonObject { ["component"] = new JsonObject { ["type"] = "application", ["name"] = "Program Kit", ["version"] = "1.0.0" } },
    ["components"] = components,
};
string sbomDigest = Write("dependency-sbom.cdx.json", sbom);

JsonObject mirror = CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(root, "eng", "dependency-mirror.lock.json"))).AsObject();
JsonArray sources = new(Directory.EnumerateFiles(Path.Combine(root, "src"), "*", SearchOption.AllDirectories)
    .Where(static path => !path.Contains($"{Path.DirectorySeparatorChar}bin{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase)
        && !path.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase))
    .OrderBy(static path => path, StringComparer.Ordinal)
    .Select(path => new JsonObject
    {
        ["logicalPath"] = Path.GetRelativePath(root, path).Replace('\\', '/'),
        ["digest"] = SourceDigest(path),
    }).ToArray());
JsonObject provenance = new()
{
    ["schema"] = "program-kit.source-package-provenance/v1",
    ["canonicalProfile"] = CanonicalJson.Profile,
    ["sourceArtifacts"] = sources,
    ["packageArtifacts"] = mirror["packages"]!.DeepClone(),
    ["sourceClosureDigest"] = CanonicalJson.Digest(sources),
    ["packageClosureDigest"] = CanonicalJson.Digest(mirror["packages"]!),
};
string provenanceDigest = Write("source-package-provenance.json", provenance);

JsonObject distribution = new()
{
    ["schema"] = "program-kit.distribution-manifest/v1",
    ["canonicalProfile"] = CanonicalJson.Profile,
    ["distribution"] = Identity(provider.Distribution),
    ["provider"] = Identity(provider.Identity),
    ["diagnosticCatalog"] = BoundArtifact(provider.DiagnosticCatalog),
    ["conformanceEvidence"] = new JsonArray(provider.ConformanceEvidence.Select(item => BoundEvidence(item)).ToArray()),
    ["artifacts"] = new JsonArray(
        Evidence("dependency-sbom.cdx.json", "application/vnd.cyclonedx+json", sbomDigest),
        Evidence("codex-diagnostic-catalog.json", "application/json", codexCatalogDigest),
        Evidence("dotnet-diagnostic-catalog.json", "application/json", providerCatalogDigest),
        Evidence("kernel-diagnostic-catalog.json", "application/json", kernelCatalogDigest),
        Evidence("provider-support.json", "application/json", supportDigest),
        Evidence("session-diagnostic-catalog.json", "application/json", sessionCatalogDigest),
        Evidence("source-package-provenance.json", "application/json", provenanceDigest)),
};
Write("distribution-manifest.json", distribution);

JsonObject Evidence(string logicalPath, string mediaType, string digest) => new()
{
    ["logicalPath"] = $"artifacts/evidence/{logicalPath}",
    ["mediaType"] = mediaType,
    ["digest"] = digest,
};

JsonObject BoundArtifact(Orbyss.ProgramKit.Contracts.Operations.ArtifactReference value) => new()
{
    ["identity"] = Identity(value.Identity),
    ["mediaType"] = value.MediaType,
    ["logicalPath"] = value.LogicalPath,
    ["digest"] = value.Digest,
    ["ownership"] = Kebab(value.Ownership.ToString()),
};

JsonObject BoundEvidence(Orbyss.ProgramKit.Contracts.Operations.EvidenceReference value) => new()
{
    ["identity"] = Identity(value.Identity),
    ["subject"] = Identity(value.Subject),
    ["profile"] = Identity(value.Profile),
    ["artifact"] = BoundArtifact(value.Artifact),
    ["freshness"] = value.Freshness,
};

string Kebab(string value)
{
    List<char> characters = new();
    for (int index = 0; index < value.Length; index++)
    {
        if (index > 0 && char.IsUpper(value[index])) characters.Add('-');
        characters.Add(char.ToLowerInvariant(value[index]));
    }
    return new string(characters.ToArray());
}
