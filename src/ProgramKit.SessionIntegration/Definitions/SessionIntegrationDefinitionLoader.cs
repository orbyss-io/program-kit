using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.SessionIntegration.Definitions;

public sealed class SessionIntegrationDefinitionLoader
{
    private readonly StructuralSchemaValidator validator = new(new SchemaRegistry());

    public CanonicalSessionIntegrationDefinition Load(string path)
    {
        JsonObject document = CanonicalJson.Parse(File.ReadAllBytes(path)) as JsonObject
            ?? throw new InvalidDataException("The session integration definition must be a JSON object.");
        if (!string.Equals(document["schema"]?.GetValue<string>(), "program-kit.session-integration-definition/v1", StringComparison.Ordinal))
            throw new InvalidDataException("The session integration definition schema is not supported.");
        string[] failures = validator.ValidateRequiredShape(ContractSchemaResources.SessionIntegrationDefinitionId, document).ToArray();
        if (failures.Length > 0) throw new InvalidDataException(string.Join("; ", failures));

        GovernedIdentity identity = ParseIdentity(document["identity"] as JsonObject ?? throw new InvalidDataException("identity is required."));
        ArtifactReference guidance = ParseArtifact(document["guidanceArtifact"] as JsonObject ?? throw new InvalidDataException("guidanceArtifact is required."));
        string fingerprint = CanonicalJson.Digest(document);
        return new CanonicalSessionIntegrationDefinition(
            "program-kit.session-integration-definition/v1",
            document["canonicalProfile"]!.GetValue<string>(),
            identity,
            ParseBindings(document["operationContracts"] as JsonArray),
            ParseBindings(document["sessionLifecycleContracts"] as JsonArray),
            guidance,
            fingerprint,
            identity.Revision);
    }

    public void DemandCompatible(CanonicalSessionIntegrationDefinition definition, string supportedRevision)
    {
        if (!string.Equals(definition.Revision, supportedRevision, StringComparison.Ordinal))
            throw new InvalidOperationException($"Definition revision {definition.Revision} is incompatible with supported revision {supportedRevision}.");
    }

    private static SessionOperationBinding[] ParseBindings(JsonArray? values) => (values ?? throw new InvalidDataException("operation bindings are required."))
        .Select(value =>
        {
            JsonObject item = value as JsonObject ?? throw new InvalidDataException("An operation binding must be an object.");
            return new SessionOperationBinding(item["name"]!.GetValue<string>(), ParseIdentity(item["contract"] as JsonObject ?? throw new InvalidDataException("contract is required.")), ParseEffect(item["effect"]!.GetValue<string>()));
        }).ToArray();

    private static EffectState ParseEffect(string value) => value switch { "none" => EffectState.None, "committed" => EffectState.Committed, _ => throw new InvalidDataException($"Unsupported effect: {value}") };

    private static GovernedIdentity ParseIdentity(JsonObject value) => new(
        value["authority"]!.GetValue<string>(), value["kind"]!.GetValue<string>(), value["name"]!.GetValue<string>(), value["revision"]!.GetValue<string>(), value["digest"]!.GetValue<string>());

    private static ArtifactReference ParseArtifact(JsonObject value) => new(
        ParseIdentity((JsonObject)value["identity"]!), value["mediaType"]!.GetValue<string>(), value["logicalPath"]!.GetValue<string>(), value["digest"]!.GetValue<string>(),
        value["ownership"]!.GetValue<string>() switch { "generated-owned" => ArtifactOwnership.GeneratedOwned, "seeded-handoff" => ArtifactOwnership.SeededHandoff, "consumer-owned" => ArtifactOwnership.ConsumerOwned, _ => throw new InvalidDataException("Unsupported ownership.") });
}
