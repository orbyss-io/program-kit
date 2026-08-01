using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Validation;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Codex;

public sealed class CodexSessionProviderManifestLoader
{
    private const string ResourceSuffix = ".Resources.codex-provider-manifest.json";
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
    private readonly StructuralSchemaValidator validator = new(new SchemaRegistry());

    public SessionProviderManifest LoadEmbedded()
    {
        Assembly assembly = typeof(CodexSessionProviderManifestLoader).Assembly;
        string name = assembly.GetManifestResourceNames().Single(resource => resource.EndsWith(ResourceSuffix, StringComparison.Ordinal));
        using Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidOperationException("The embedded Codex provider manifest is missing.");
        using MemoryStream buffer = new();
        stream.CopyTo(buffer);
        return Load(buffer.ToArray());
    }

    public SessionProviderManifest Load(ReadOnlySpan<byte> bytes)
    {
        JsonObject document = CanonicalJson.Parse(bytes) as JsonObject
            ?? throw new InvalidDataException("The Codex provider manifest must be a JSON object.");
        DemandProperties(document, "manifest", "schema", "canonicalProfile", "providerIdentity", "adapterIdentity", "definitionBinding", "bindingKind", "supportedScopes", "providerSurface", "projectionDescriptors", "requiredOperations", "diagnosticCatalog", "conformanceProfile", "supportClaim");
        if (!string.Equals(RequiredString(document, "schema"), "program-kit.session-provider-manifest/v1", StringComparison.Ordinal) ||
            !string.Equals(RequiredString(document, "canonicalProfile"), CanonicalJson.Profile, StringComparison.Ordinal))
            throw new InvalidDataException("The Codex provider manifest schema or canonical profile is unsupported.");
        string[] failures = validator.ValidateRequiredShape(ContractSchemaResources.SessionProviderManifestId, document).ToArray();
        if (failures.Length > 0) throw new InvalidDataException(string.Join("; ", failures));

        GovernedIdentity provider = ParseIdentity(RequiredObject(document, "providerIdentity"));
        GovernedIdentity adapter = ParseIdentity(RequiredObject(document, "adapterIdentity"));
        GovernedIdentity definition = ParseIdentity(RequiredObject(document, "definitionBinding"));
        GovernedIdentity diagnostic = ParseIdentity(RequiredObject(document, "diagnosticCatalog"));
        GovernedIdentity conformance = ParseIdentity(RequiredObject(document, "conformanceProfile"));
        DemandIdentity(provider, "session-provider");
        DemandIdentity(adapter, "session-provider-adapter");
        DemandIdentity(definition, "session-integration-definition");
        DemandIdentity(diagnostic, "diagnostic-catalog");
        DemandIdentity(conformance, "session-provider-conformance");

        JsonObject normalized = (JsonObject)document.DeepClone();
        normalized["providerIdentity"]!["digest"] = EmptyDigest;
        normalized["adapterIdentity"]!["digest"] = EmptyDigest;
        string manifestDigest = CanonicalJson.Digest(normalized);
        if (!string.Equals(provider.Digest, manifestDigest, StringComparison.Ordinal) ||
            !string.Equals(adapter.Digest, manifestDigest, StringComparison.Ordinal))
            throw new InvalidDataException("The provider and adapter identities must bind the exact normalized manifest content.");
        if (!Exact(definition, CanonicalSessionGuidance.Definition.Identity))
            throw new InvalidDataException("The provider manifest definition binding is not exact.");
        if (!Exact(conformance, SessionProviderConformanceProfiles.RepositoryWorkspaceV1.Identity))
            throw new InvalidDataException("The provider manifest conformance profile is not the executable profile.");

        string diagnosticContent = string.Join('\n', CodexDiagnosticCatalog.Entries.OrderBy(static item => item.Key, StringComparer.Ordinal).Select(static item => $"{item.Key}={item.Value}"));
        if (!string.Equals(diagnostic.Digest, Digests.Sha256(Encoding.UTF8.GetBytes(diagnosticContent)), StringComparison.Ordinal))
            throw new InvalidDataException("The provider diagnostic identity does not match the executable catalog.");

        string binding = RequiredString(document, "bindingKind");
        if (!string.Equals(binding, "shell-cli", StringComparison.Ordinal))
            throw new InvalidDataException("The provider binding kind is unsupported.");
        string[] scopes = ParseStrings(RequiredArray(document, "supportedScopes"), "supportedScopes");
        DemandSet(scopes, new[] { "workspace" }, "supportedScopes");

        JsonObject surfaceValue = RequiredObject(document, "providerSurface");
        DemandProperties(surfaceValue, "providerSurface", "providerName", "surfaceName", "surfaceRevision", "testedVersions", "discovery", "reloadBehavior", "structuredResultTransport");
        SessionProviderSurface surface = new(
            RequiredString(surfaceValue, "providerName"),
            RequiredString(surfaceValue, "surfaceName"),
            RequiredString(surfaceValue, "surfaceRevision"),
            ParseStrings(RequiredArray(surfaceValue, "testedVersions"), "testedVersions"),
            RequiredString(surfaceValue, "discovery"),
            RequiredString(surfaceValue, "reloadBehavior"),
            RequiredString(surfaceValue, "structuredResultTransport"));
        if (!string.Equals(surface.ProviderName, "Codex", StringComparison.Ordinal) ||
            !string.Equals(surface.SurfaceName, "repository-skill", StringComparison.Ordinal) ||
            surface.TestedVersions.Count == 0 ||
            !string.Equals(surface.Discovery, "repository-skill", StringComparison.Ordinal) ||
            !string.Equals(surface.ReloadBehavior, "automatic-or-fresh-session", StringComparison.Ordinal) ||
            !string.Equals(surface.StructuredResultTransport, "json-stdout", StringComparison.Ordinal))
            throw new InvalidDataException("The Codex provider surface is incomplete or unsupported.");

        SessionProjectionDescriptor[] descriptors = RequiredArray(document, "projectionDescriptors").Select(value =>
        {
            JsonObject item = value as JsonObject ?? throw new InvalidDataException("A projection descriptor must be an object.");
            DemandProperties(item, "projection descriptor", "role", "logicalPath", "mediaType", "ownership", "claimClass", "removalPolicy");
            if (!string.Equals(RequiredString(item, "ownership"), "generated-owned", StringComparison.Ordinal) ||
                !string.Equals(RequiredString(item, "claimClass"), "canonical-byte", StringComparison.Ordinal))
                throw new InvalidDataException("The provider projection ownership or claim class is unsupported.");
            return new SessionProjectionDescriptor(
                RequiredString(item, "role"),
                RequiredString(item, "logicalPath"),
                RequiredString(item, "mediaType"),
                ArtifactOwnership.GeneratedOwned,
                ClaimClass.CanonicalByte,
                RequiredString(item, "removalPolicy"));
        }).ToArray();
        if (descriptors.Length == 0 || descriptors.Select(static item => item.LogicalPath).Distinct(StringComparer.Ordinal).Count() != descriptors.Length)
            throw new InvalidDataException("The provider projection descriptors must be non-empty and unique.");

        string[] operations = ParseStrings(RequiredArray(document, "requiredOperations"), "requiredOperations");
        DemandSet(operations, SessionProviderConformanceProfiles.RepositoryWorkspaceV1.RequiredOperations, "requiredOperations");
        SessionProviderSupport support = RequiredString(document, "supportClaim") switch
        {
            "supported" => SessionProviderSupport.Supported,
            "incompatible" => SessionProviderSupport.Incompatible,
            "not-evaluated" => SessionProviderSupport.NotEvaluated,
            _ => throw new InvalidDataException("The provider support claim is unsupported."),
        };

        return new SessionProviderManifest(
            "program-kit.session-provider-manifest/v1",
            CanonicalJson.Profile,
            provider,
            adapter,
            definition,
            SessionBindingKind.ShellCli,
            scopes,
            surface,
            descriptors,
            operations,
            diagnostic,
            conformance,
            support,
            surface.SurfaceRevision,
            adapter.Revision);
    }

    private static GovernedIdentity ParseIdentity(JsonObject value)
    {
        DemandProperties(value, "governed identity", "authority", "kind", "name", "revision", "digest");
        return new GovernedIdentity(RequiredString(value, "authority"), RequiredString(value, "kind"), RequiredString(value, "name"), RequiredString(value, "revision"), RequiredString(value, "digest"));
    }

    private static void DemandIdentity(GovernedIdentity identity, string kind)
    {
        if (!string.Equals(identity.Kind, kind, StringComparison.Ordinal) ||
            string.IsNullOrWhiteSpace(identity.Authority) ||
            string.IsNullOrWhiteSpace(identity.Name) ||
            string.IsNullOrWhiteSpace(identity.Revision) ||
            !IsDigest(identity.Digest) ||
            string.Equals(identity.Digest, EmptyDigest, StringComparison.Ordinal))
            throw new InvalidDataException($"The {kind} identity is incomplete or uses a placeholder digest.");
    }

    private static bool IsDigest(string value) =>
        value.Length == 71 &&
        value.StartsWith("sha256:", StringComparison.Ordinal) &&
        value[7..].All(static character => character is >= '0' and <= '9' or >= 'a' and <= 'f');

    private static bool Exact(GovernedIdentity left, GovernedIdentity right) =>
        string.Equals(left.Authority, right.Authority, StringComparison.Ordinal) &&
        string.Equals(left.Kind, right.Kind, StringComparison.Ordinal) &&
        string.Equals(left.Name, right.Name, StringComparison.Ordinal) &&
        string.Equals(left.Revision, right.Revision, StringComparison.Ordinal) &&
        string.Equals(left.Digest, right.Digest, StringComparison.Ordinal);

    private static string[] ParseStrings(JsonArray value, string subject)
    {
        string[] result = value.Select(item => item?.GetValue<string>() ?? throw new InvalidDataException($"{subject} must contain strings.")).ToArray();
        if (result.Distinct(StringComparer.Ordinal).Count() != result.Length)
            throw new InvalidDataException($"{subject} must not contain duplicates.");
        return result;
    }

    private static void DemandSet(IEnumerable<string> observed, IEnumerable<string> expected, string subject)
    {
        if (!observed.OrderBy(static item => item, StringComparer.Ordinal).SequenceEqual(expected.OrderBy(static item => item, StringComparer.Ordinal), StringComparer.Ordinal))
            throw new InvalidDataException($"{subject} does not match the governed set.");
    }

    private static void DemandProperties(JsonObject value, string subject, params string[] expected)
    {
        if (!value.Select(static item => item.Key).OrderBy(static item => item, StringComparer.Ordinal).SequenceEqual(expected.OrderBy(static item => item, StringComparer.Ordinal), StringComparer.Ordinal))
            throw new InvalidDataException($"{subject} properties do not match the governed contract.");
    }

    private static JsonObject RequiredObject(JsonObject value, string property) => value[property] as JsonObject ?? throw new InvalidDataException($"{property} must be an object.");
    private static JsonArray RequiredArray(JsonObject value, string property) => value[property] as JsonArray ?? throw new InvalidDataException($"{property} must be an array.");
    private static string RequiredString(JsonObject value, string property) => value[property]?.GetValue<string>() ?? throw new InvalidDataException($"{property} must be a string.");
}
