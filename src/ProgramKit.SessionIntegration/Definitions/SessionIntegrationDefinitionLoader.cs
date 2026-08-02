using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Validation;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Definitions;

public sealed class SessionIntegrationDefinitionLoader
{
    public const string DefinitionResourceSuffix = ".Resources.session-integration-definition.json";
    public const string GuidanceResourceSuffix = ".Resources.session-guidance.md";
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
    private readonly StructuralSchemaValidator validator = new(new SchemaRegistry());

    public CanonicalSessionIntegrationDefinition LoadEmbedded()
    {
        Assembly assembly = typeof(SessionIntegrationDefinitionLoader).Assembly;
        return Load(ReadResource(assembly, DefinitionResourceSuffix), ReadResource(assembly, GuidanceResourceSuffix));
    }

    public CanonicalSessionIntegrationDefinition Load(string definitionPath, string guidancePath) =>
        Load(File.ReadAllBytes(definitionPath), File.ReadAllBytes(guidancePath));

    public CanonicalSessionIntegrationDefinition Load(ReadOnlySpan<byte> definitionBytes, ReadOnlySpan<byte> guidanceBytes)
    {
        JsonObject document = CanonicalJson.Parse(definitionBytes) as JsonObject
            ?? throw new InvalidDataException("The session integration definition must be a JSON object.");
        DemandProperties(document, "definition", "schema", "canonicalProfile", "identity", "operationContracts", "sessionLifecycleContracts", "authorityRules", "effectClasses", "resultRules", "guidanceArtifact", "projectionRequirements", "diagnosticCatalogs");
        DemandExact(document, "schema", "program-kit.session-integration-definition/v1");
        DemandExact(document, "canonicalProfile", CanonicalJson.Profile);
        string[] failures = validator.ValidateRequiredShape(ContractSchemaResources.SessionIntegrationDefinitionId, document).ToArray();
        if (failures.Length > 0) throw new InvalidDataException(string.Join("; ", failures));

        GovernedIdentity identity = ParseIdentity(RequiredObject(document, "identity"));
        DemandIdentity(identity, "session-integration-definition", "definition identity");
        JsonObject normalized = (JsonObject)document.DeepClone();
        normalized["identity"]!["digest"] = EmptyDigest;
        string fingerprint = CanonicalJson.Digest(normalized);
        if (!string.Equals(identity.Digest, fingerprint, StringComparison.Ordinal))
            throw new InvalidDataException("The session definition identity digest does not match its normalized canonical content.");

        SessionOperationBinding[] operations = ParseBindings(RequiredArray(document, "operationContracts"));
        SessionOperationBinding[] lifecycle = ParseBindings(RequiredArray(document, "sessionLifecycleContracts"));
        DemandBindings(operations, new Dictionary<string, EffectState>(StringComparer.Ordinal)
        {
            ["explain"] = EffectState.None,
            ["construct"] = EffectState.Committed,
            ["evaluate"] = EffectState.None,
        }, "operationContracts");
        DemandBindings(lifecycle, new Dictionary<string, EffectState>(StringComparer.Ordinal)
        {
            ["session-explain"] = EffectState.None,
            ["session-install"] = EffectState.Committed,
            ["session-verify"] = EffectState.None,
            ["session-remove"] = EffectState.Committed,
        }, "sessionLifecycleContracts");

        JsonObject authority = RequiredObject(document, "authorityRules");
        DemandProperties(authority, "authorityRules", "humanApprovalRequiredFor", "requestBindingRequired", "ambientAuthorityForbidden", "grantReuseForbidden");
        SessionAuthorityRules authorityRules = new(
            ParseStrings(RequiredArray(authority, "humanApprovalRequiredFor"), "humanApprovalRequiredFor"),
            DemandBoolean(authority, "requestBindingRequired", true),
            DemandBoolean(authority, "ambientAuthorityForbidden", true),
            DemandBoolean(authority, "grantReuseForbidden", true));
        DemandSet(authorityRules.HumanApprovalRequiredFor, new[] { "construct", "session-install", "session-remove" }, "humanApprovalRequiredFor");

        JsonObject effects = RequiredObject(document, "effectClasses");
        DemandProperties(effects, "effectClasses", "readOnly", "effectBearing");
        SessionEffectClasses effectClasses = new(
            ParseStrings(RequiredArray(effects, "readOnly"), "readOnly"),
            ParseStrings(RequiredArray(effects, "effectBearing"), "effectBearing"));
        DemandSet(effectClasses.ReadOnly, new[] { "explain", "evaluate", "session-explain", "session-verify" }, "readOnly");
        DemandSet(effectClasses.EffectBearing, new[] { "construct", "session-install", "session-remove" }, "effectBearing");

        JsonObject result = RequiredObject(document, "resultRules");
        DemandProperties(result, "resultRules", "schema", "authoritativeChannel", "requiredFields", "renderedProseAuthoritative", "diagnosticIdentityRequired");
        SessionResultRules resultRules = new(
            ParseIdentity(RequiredObject(result, "schema")),
            RequiredString(result, "authoritativeChannel"),
            ParseStrings(RequiredArray(result, "requiredFields"), "requiredFields"),
            DemandBoolean(result, "renderedProseAuthoritative", false),
            DemandBoolean(result, "diagnosticIdentityRequired", true));
        DemandIdentity(resultRules.Schema, "schema", "result schema");
        if (!string.Equals(resultRules.AuthoritativeChannel, "json-stdout", StringComparison.Ordinal))
            throw new InvalidDataException("The authoritative result channel must be json-stdout.");
        DemandSet(resultRules.RequiredFields, new[] { "outcome", "furthestPhase", "effectState", "primaryDisposition", "artifacts", "evidence", "receipts", "diagnostics" }, "requiredFields");

        ArtifactReference guidance = ParseArtifact(RequiredObject(document, "guidanceArtifact"));
        string observedGuidance = Digests.Sha256(guidanceBytes);
        if (!string.Equals(guidance.Digest, observedGuidance, StringComparison.Ordinal) ||
            !string.Equals(guidance.Identity.Digest, observedGuidance, StringComparison.Ordinal))
            throw new InvalidDataException("The canonical guidance artifact digest does not match the embedded guidance bytes.");
        if (guidance.Ownership != ArtifactOwnership.GeneratedOwned ||
            !string.Equals(guidance.MediaType, "text/markdown", StringComparison.Ordinal) ||
            !string.Equals(guidance.LogicalPath, "canonical/session-guidance.md", StringComparison.Ordinal))
            throw new InvalidDataException("The canonical guidance artifact contract is unsupported.");

        JsonObject projection = RequiredObject(document, "projectionRequirements");
        DemandProperties(projection, "projectionRequirements", "scope", "workingDirectory", "cleanStructuredOutput", "reloadStateReported", "providerFieldsCanonical", "domainSemanticsAllowed");
        SessionProjectionRequirements projectionRequirements = new(
            RequiredString(projection, "scope"),
            RequiredString(projection, "workingDirectory"),
            DemandBoolean(projection, "cleanStructuredOutput", true),
            DemandBoolean(projection, "reloadStateReported", true),
            DemandBoolean(projection, "providerFieldsCanonical", false),
            DemandBoolean(projection, "domainSemanticsAllowed", false));
        if (!string.Equals(projectionRequirements.Scope, "workspace", StringComparison.Ordinal) ||
            !string.Equals(projectionRequirements.WorkingDirectory, "workspace-root", StringComparison.Ordinal))
            throw new InvalidDataException("The canonical projection scope or working-directory rule is unsupported.");

        GovernedIdentity[] catalogs = RequiredArray(document, "diagnosticCatalogs")
            .Select(value => ParseIdentity(value as JsonObject ?? throw new InvalidDataException("Each diagnostic catalog must be an object.")))
            .ToArray();
        if (catalogs.Length != 2 || catalogs.Select(static item => item.StableKey).Distinct(StringComparer.Ordinal).Count() != catalogs.Length)
            throw new InvalidDataException("Exactly the kernel and session diagnostic catalogs are required.");
        foreach (GovernedIdentity catalog in catalogs) DemandIdentity(catalog, "diagnostic-catalog", "diagnostic catalog");
        if (!catalogs.Any(static catalog => Exact(catalog, DiagnosticCatalogArtifacts.KernelIdentity)) ||
            !catalogs.Any(static catalog => Exact(catalog, SessionDiagnosticCatalog.Identity)))
            throw new InvalidDataException("The session definition diagnostic catalog bindings are not exact executable identities.");

        return new CanonicalSessionIntegrationDefinition(
            "program-kit.session-integration-definition/v1",
            CanonicalJson.Profile,
            identity,
            operations,
            lifecycle,
            authorityRules,
            effectClasses,
            resultRules,
            guidance,
            projectionRequirements,
            catalogs,
            fingerprint,
            identity.Revision);
    }

    public void DemandCompatible(CanonicalSessionIntegrationDefinition definition, GovernedIdentity selected)
    {
        if (!Exact(definition.Identity, selected))
            throw new InvalidOperationException("The selected canonical definition identity is not exact.");
    }

    public static byte[] ReadEmbeddedGuidance() => ReadResource(typeof(SessionIntegrationDefinitionLoader).Assembly, GuidanceResourceSuffix);

    private static byte[] ReadResource(Assembly assembly, string suffix)
    {
        string name = assembly.GetManifestResourceNames().Single(resource => resource.EndsWith(suffix, StringComparison.Ordinal));
        using Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidOperationException($"Missing embedded resource: {suffix}");
        using MemoryStream buffer = new();
        stream.CopyTo(buffer);
        return buffer.ToArray();
    }

    private static SessionOperationBinding[] ParseBindings(JsonArray values) => values.Select(value =>
    {
        JsonObject item = value as JsonObject ?? throw new InvalidDataException("An operation binding must be an object.");
        DemandProperties(item, "operation binding", "name", "contract", "effect");
        return new SessionOperationBinding(RequiredString(item, "name"), ParseIdentity(RequiredObject(item, "contract")), ParseEffect(RequiredString(item, "effect")));
    }).ToArray();

    private static void DemandBindings(IReadOnlyList<SessionOperationBinding> observed, IReadOnlyDictionary<string, EffectState> expected, string subject)
    {
        if (observed.Count != expected.Count || observed.Select(static item => item.Name).Distinct(StringComparer.Ordinal).Count() != observed.Count)
            throw new InvalidDataException($"{subject} must contain each governed operation exactly once.");
        foreach (SessionOperationBinding binding in observed)
        {
            if (!expected.TryGetValue(binding.Name, out EffectState effect) || binding.Effect != effect)
                throw new InvalidDataException($"{subject} contains an unsupported operation or effect.");
            DemandIdentity(binding.Contract, "operation-contract", $"{subject} contract");
            if (!string.Equals(binding.Contract.Name, binding.Name, StringComparison.Ordinal))
                throw new InvalidDataException($"{subject} contract identity does not match its operation name.");
        }
    }

    private static ArtifactReference ParseArtifact(JsonObject value)
    {
        DemandProperties(value, "artifact reference", "identity", "mediaType", "logicalPath", "digest", "ownership");
        GovernedIdentity identity = ParseIdentity(RequiredObject(value, "identity"));
        DemandIdentity(identity, identity.Kind, "artifact identity");
        string digest = RequiredString(value, "digest");
        DemandDigest(digest, "artifact digest");
        return new ArtifactReference(
            identity,
            RequiredString(value, "mediaType"),
            RequiredString(value, "logicalPath"),
            digest,
            RequiredString(value, "ownership") switch
            {
                "generated-owned" => ArtifactOwnership.GeneratedOwned,
                "seeded-handoff" => ArtifactOwnership.SeededHandoff,
                "consumer-owned" => ArtifactOwnership.ConsumerOwned,
                _ => throw new InvalidDataException("Unsupported artifact ownership."),
            });
    }

    private static GovernedIdentity ParseIdentity(JsonObject value)
    {
        DemandProperties(value, "governed identity", "authority", "kind", "name", "revision", "digest");
        return new GovernedIdentity(RequiredString(value, "authority"), RequiredString(value, "kind"), RequiredString(value, "name"), RequiredString(value, "revision"), RequiredString(value, "digest"));
    }

    private static void DemandIdentity(GovernedIdentity identity, string kind, string subject)
    {
        if (!string.Equals(identity.Kind, kind, StringComparison.Ordinal))
            throw new InvalidDataException($"{subject} has an unsupported kind.");
        if (string.IsNullOrWhiteSpace(identity.Authority) || string.IsNullOrWhiteSpace(identity.Name) || string.IsNullOrWhiteSpace(identity.Revision))
            throw new InvalidDataException($"{subject} is incomplete.");
        DemandDigest(identity.Digest, $"{subject} digest");
    }

    private static void DemandDigest(string value, string subject)
    {
        if (value.Length != 71 || !value.StartsWith("sha256:", StringComparison.Ordinal) ||
            value[7..].Any(static character => !char.IsAsciiHexDigitLower(character)) || string.Equals(value, EmptyDigest, StringComparison.Ordinal))
            throw new InvalidDataException($"{subject} must be a non-placeholder lowercase SHA-256 digest.");
    }

    private static bool Exact(GovernedIdentity left, GovernedIdentity right) =>
        string.Equals(left.Authority, right.Authority, StringComparison.Ordinal) &&
        string.Equals(left.Kind, right.Kind, StringComparison.Ordinal) &&
        string.Equals(left.Name, right.Name, StringComparison.Ordinal) &&
        string.Equals(left.Revision, right.Revision, StringComparison.Ordinal) &&
        string.Equals(left.Digest, right.Digest, StringComparison.Ordinal);

    private static EffectState ParseEffect(string value) => value switch
    {
        "none" => EffectState.None,
        "committed" => EffectState.Committed,
        _ => throw new InvalidDataException($"Unsupported effect: {value}"),
    };

    private static void DemandProperties(JsonObject value, string subject, params string[] expected)
    {
        string[] observed = value.Select(static item => item.Key).OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        string[] required = expected.OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        if (!observed.SequenceEqual(required, StringComparer.Ordinal))
            throw new InvalidDataException($"{subject} properties do not match the governed contract.");
    }

    private static void DemandExact(JsonObject value, string property, string expected)
    {
        if (!string.Equals(RequiredString(value, property), expected, StringComparison.Ordinal))
            throw new InvalidDataException($"{property} is unsupported.");
    }

    private static bool DemandBoolean(JsonObject value, string property, bool expected)
    {
        bool observed = value[property]?.GetValue<bool>() ?? throw new InvalidDataException($"{property} is required.");
        if (observed != expected) throw new InvalidDataException($"{property} must be {expected.ToString().ToLowerInvariant()}.");
        return observed;
    }

    private static IReadOnlyList<string> ParseStrings(JsonArray value, string subject)
    {
        string[] items = value.Select(item => item?.GetValue<string>() ?? throw new InvalidDataException($"{subject} contains a non-string value.")).ToArray();
        if (items.Distinct(StringComparer.Ordinal).Count() != items.Length)
            throw new InvalidDataException($"{subject} contains duplicate values.");
        return items;
    }

    private static void DemandSet(IReadOnlyList<string> observed, IEnumerable<string> expected, string subject)
    {
        if (!observed.OrderBy(static item => item, StringComparer.Ordinal).SequenceEqual(expected.OrderBy(static item => item, StringComparer.Ordinal), StringComparer.Ordinal))
            throw new InvalidDataException($"{subject} does not match the canonical governed set.");
    }

    private static JsonObject RequiredObject(JsonObject value, string property) =>
        value[property] as JsonObject ?? throw new InvalidDataException($"{property} must be an object.");

    private static JsonArray RequiredArray(JsonObject value, string property) =>
        value[property] as JsonArray ?? throw new InvalidDataException($"{property} must be an array.");

    private static string RequiredString(JsonObject value, string property) =>
        value[property]?.GetValue<string>() ?? throw new InvalidDataException($"{property} must be a string.");
}
