using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Validation;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Manifest;

public sealed class ClaudeProviderManifestLoader
{
    private const string ResourceSuffix = ".Manifest.claude-code-provider-manifest.json";
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
    private readonly StructuralSchemaValidator validator = new(new SchemaRegistry());

    public SessionProviderManifest LoadEmbedded()
    {
        Assembly assembly = typeof(ClaudeProviderManifestLoader).Assembly;
        string name = assembly.GetManifestResourceNames().Single(item => item.EndsWith(ResourceSuffix, StringComparison.Ordinal));
        using Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidOperationException("The embedded Claude provider manifest is missing.");
        using MemoryStream buffer = new();
        stream.CopyTo(buffer);
        return Load(buffer.ToArray());
    }

    public SessionProviderManifest Load(ReadOnlySpan<byte> bytes)
    {
        JsonObject document = CanonicalJson.Parse(bytes) as JsonObject
            ?? throw new InvalidDataException("The Claude provider manifest must be a JSON object.");
        DemandProperties(document, "manifest", "schema", "canonicalProfile", "providerIdentity", "adapterIdentity", "definitionBinding", "bindingKind", "supportedScopes", "providerSurface", "projectionDescriptors", "requiredOperations", "diagnosticCatalog", "conformanceProfile", "supportClaim");
        if (!string.Equals(RequiredString(document, "schema"), "program-kit.session-provider-manifest/v1", StringComparison.Ordinal) ||
            !string.Equals(RequiredString(document, "canonicalProfile"), CanonicalJson.Profile, StringComparison.Ordinal))
            throw new InvalidDataException("The Claude provider manifest schema or canonical profile is unsupported.");
        string[] shapeFailures = validator.ValidateRequiredShape(ContractSchemaResources.SessionProviderManifestId, document).ToArray();
        if (shapeFailures.Length > 0) throw new InvalidDataException(string.Join("; ", shapeFailures));

        GovernedIdentity provider = ParseIdentity(RequiredObject(document, "providerIdentity"));
        GovernedIdentity adapter = ParseIdentity(RequiredObject(document, "adapterIdentity"));
        GovernedIdentity definition = ParseIdentity(RequiredObject(document, "definitionBinding"));
        GovernedIdentity diagnostic = ParseIdentity(RequiredObject(document, "diagnosticCatalog"));
        GovernedIdentity conformance = ParseIdentity(RequiredObject(document, "conformanceProfile"));

        JsonObject normalized = (JsonObject)document.DeepClone();
        normalized["providerIdentity"]!["digest"] = EmptyDigest;
        normalized["adapterIdentity"]!["digest"] = EmptyDigest;
        string manifestDigest = CanonicalJson.Digest(normalized);
        DemandExactIdentity(provider, ClaudeProviderIdentities.Provider(manifestDigest), "provider");
        DemandExactIdentity(adapter, ClaudeProviderIdentities.Adapter(manifestDigest), "adapter");
        DemandExactIdentity(definition, CanonicalSessionGuidance.Definition.Identity, "definition");
        DemandExactIdentity(conformance, SessionProviderConformanceProfiles.RepositoryWorkspaceV1.Identity, "conformance profile");
        if (!string.Equals(diagnostic.Authority, "orbyss.program-kit.claude-code", StringComparison.Ordinal) ||
            !string.Equals(diagnostic.Kind, "diagnostic-catalog", StringComparison.Ordinal) ||
            !string.Equals(diagnostic.Name, "session-provider", StringComparison.Ordinal) ||
            !string.Equals(diagnostic.Revision, ClaudeDiagnosticCatalog.Version, StringComparison.Ordinal) ||
            !string.Equals(diagnostic.Digest, ClaudeDiagnosticCatalog.Digest, StringComparison.Ordinal))
            throw new InvalidDataException("The Claude diagnostic catalog identity is not exact.");

        if (!string.Equals(RequiredString(document, "bindingKind"), "shell-cli", StringComparison.Ordinal))
            throw new InvalidDataException("The Claude binding kind is unsupported.");
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
        if (!string.Equals(surface.ProviderName, "Claude Code", StringComparison.Ordinal) ||
            !string.Equals(surface.SurfaceName, "project-skill", StringComparison.Ordinal) ||
            !string.Equals(surface.SurfaceRevision, ClaudeProviderIdentities.ProviderVersion, StringComparison.Ordinal) ||
            !surface.TestedVersions.SequenceEqual(new[] { ClaudeProviderIdentities.ProviderVersion }, StringComparer.Ordinal) ||
            !string.Equals(surface.Discovery, "project-skill", StringComparison.Ordinal) ||
            !string.Equals(surface.ReloadBehavior, "fresh-session", StringComparison.Ordinal) ||
            !string.Equals(surface.StructuredResultTransport, "json-stdout", StringComparison.Ordinal))
            throw new InvalidDataException("The Claude provider surface is incomplete or unsupported.");

        SessionProjectionDescriptor[] descriptors = RequiredArray(document, "projectionDescriptors").Select(value =>
        {
            JsonObject item = value as JsonObject ?? throw new InvalidDataException("A Claude projection descriptor must be an object.");
            DemandProperties(item, "projection descriptor", "role", "logicalPath", "mediaType", "ownership", "claimClass", "removalPolicy");
            return new SessionProjectionDescriptor(
                RequiredString(item, "role"), RequiredString(item, "logicalPath"), RequiredString(item, "mediaType"),
                ParseOwnership(RequiredString(item, "ownership")), ParseClaim(RequiredString(item, "claimClass")), RequiredString(item, "removalPolicy"));
        }).ToArray();
        if (descriptors.Length != 1 ||
            !string.Equals(descriptors[0].Role, "session-capability", StringComparison.Ordinal) ||
            !string.Equals(descriptors[0].LogicalPath, ClaudeProviderIdentities.SkillLogicalPath, StringComparison.Ordinal) ||
            !string.Equals(descriptors[0].MediaType, "text/markdown", StringComparison.Ordinal) ||
            descriptors[0].Ownership != ArtifactOwnership.GeneratedOwned ||
            descriptors[0].ClaimClass != ClaimClass.CanonicalByte ||
            !string.Equals(descriptors[0].RemovalPolicy, "exact-admitted-digest-only", StringComparison.Ordinal))
            throw new InvalidDataException("The Claude projection descriptor is not exact.");

        string[] operations = ParseStrings(RequiredArray(document, "requiredOperations"), "requiredOperations");
        DemandSet(operations, SessionProviderConformanceProfiles.RepositoryWorkspaceV1.RequiredOperations, "requiredOperations");
        if (!string.Equals(RequiredString(document, "supportClaim"), "not-evaluated", StringComparison.Ordinal))
            throw new InvalidDataException("This Feature 003 manifest must remain fail-closed while Feature 002 is rejected.");

        return new SessionProviderManifest(
            "program-kit.session-provider-manifest/v1", CanonicalJson.Profile, provider, adapter, definition,
            SessionBindingKind.ShellCli, scopes, surface, descriptors, operations, diagnostic, conformance,
            SessionProviderSupport.NotEvaluated, surface.SurfaceRevision, adapter.Revision);
    }

    private static ArtifactOwnership ParseOwnership(string value) => value == "generated-owned" ? ArtifactOwnership.GeneratedOwned : throw new InvalidDataException("The Claude projection ownership is unsupported.");
    private static ClaimClass ParseClaim(string value) => value == "canonical-byte" ? ClaimClass.CanonicalByte : throw new InvalidDataException("The Claude projection claim class is unsupported.");

    private static GovernedIdentity ParseIdentity(JsonObject value)
    {
        DemandProperties(value, "governed identity", "authority", "kind", "name", "revision", "digest");
        return new(RequiredString(value, "authority"), RequiredString(value, "kind"), RequiredString(value, "name"), RequiredString(value, "revision"), RequiredString(value, "digest"));
    }

    private static void DemandExactIdentity(GovernedIdentity observed, GovernedIdentity expected, string subject)
    {
        if (observed != expected) throw new InvalidDataException($"The Claude {subject} identity is not exact; expected digest {expected.Digest}.");
    }

    private static string[] ParseStrings(JsonArray value, string subject)
    {
        string[] result = value.Select(item => item?.GetValue<string>() ?? throw new InvalidDataException($"{subject} must contain strings.")).ToArray();
        if (result.Distinct(StringComparer.Ordinal).Count() != result.Length) throw new InvalidDataException($"{subject} must not contain duplicates.");
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
