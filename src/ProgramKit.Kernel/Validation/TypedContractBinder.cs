using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;

namespace Orbyss.ProgramKit.Kernel.Validation;

public sealed class TypedContractBinder
{
    public FactoryRequest BindFactoryRequest(JsonObject document)
    {
        string schema = RequiredString(document, "schema");
        if (!string.Equals(schema, "program-kit.factory-request/v1", StringComparison.Ordinal))
        {
            throw new InvalidDataException("Unsupported factory-request schema.");
        }

        string canonicalProfile = RequiredString(document, "canonicalProfile");
        if (!string.Equals(canonicalProfile, "program-kit.canonical-json/v1", StringComparison.Ordinal))
        {
            throw new InvalidDataException("Unsupported canonical profile.");
        }

        FactoryOperation operation = ParseEnum<FactoryOperation>(RequiredString(document, "operation"));
        RequestedEffect effect = ParseEnum<RequestedEffect>(RequiredString(document, "requestedEffect"));
        ConstructionMode? mode = document["constructionMode"] is null
            ? null
            : ParseEnum<ConstructionMode>(RequiredString(document, "constructionMode"));
        if ((operation == FactoryOperation.Construct) != (mode is not null))
        {
            throw new InvalidDataException("constructionMode is required only for construct.");
        }

        if (operation != FactoryOperation.Construct && effect != RequestedEffect.None)
        {
            throw new InvalidDataException("Explain and evaluate requests must have requestedEffect none.");
        }

        JsonObject evaluation = RequiredObject(document, "evaluationContext");
        DateTimeOffset instant = ParseInstant(evaluation, "instant");
        string assurance = RequiredString(evaluation, "assurance");
        if (!string.Equals(assurance, "approved-declared-instant", StringComparison.Ordinal))
        {
            throw new InvalidDataException("Unsupported evaluation-context assurance.");
        }

        ArtifactReference rootBundle = BindArtifact(RequiredObject(document, "rootBundle"));
        GovernedIdentity workspace = BindIdentity(RequiredObject(document, "workspaceIdentity"));
        EvaluationContext context = new(instant, BindIdentity(RequiredObject(evaluation, "source")), assurance);
        ExactSelection[] selections = RequiredArray(document, "selections")
            .Select((node, index) => BindSelection(node as JsonObject ?? throw new InvalidDataException($"selections[{index}] must be an object.")))
            .OrderBy(static selection => selection.Role, StringComparer.Ordinal)
            .ToArray();
        if (selections.Select(static item => item.Role).Distinct(StringComparer.Ordinal).Count() != selections.Length)
        {
            throw new ProgramKitDiagnosticException(DiagnosticIds.AmbiguousSelection, OperationPhase.Validation, PrimaryDisposition.ProvideInput, "Every selection role must occur exactly once.");
        }

        ArtifactReference? authority = document["authorityGrant"] is JsonObject authorityObject
            ? BindArtifact(authorityObject)
            : null;
        ExpectedState? expected = document["expectedState"] is JsonObject expectedObject
            ? new ExpectedState(RequiredString(expectedObject, "closureDigest"), RequiredString(expectedObject, "liveStateDigest"))
            : null;
        if (effect != RequestedEffect.None && (authority is null || expected is null))
        {
            throw new InvalidDataException("Effectful requests require exact authorityGrant and expectedState bindings.");
        }

        ArtifactReference? continuation = document["continuation"] is JsonObject continuationObject
            ? BindArtifact(continuationObject)
            : null;

        return new FactoryRequest(schema, canonicalProfile, operation, mode, rootBundle, workspace, context, effect, selections, authority, expected, continuation);
    }

    public ArtifactReference BindArtifact(JsonObject document) => new(
        BindIdentity(RequiredObject(document, "identity")),
        RequiredString(document, "mediaType"),
        RequiredString(document, "logicalPath"),
        RequiredString(document, "digest"),
        ParseEnum<ArtifactOwnership>(RequiredString(document, "ownership")));

    public GovernedIdentity BindIdentity(JsonObject document) => new(
        RequiredString(document, "authority"),
        RequiredString(document, "kind"),
        RequiredString(document, "name"),
        RequiredString(document, "revision"),
        RequiredString(document, "digest"));

    private ExactSelection BindSelection(JsonObject document) => new(
        RequiredString(document, "role"),
        BindIdentity(RequiredObject(document, "selected")),
        BindIdentity(RequiredObject(document, "selectionAuthority")),
        BindTrace(RequiredObject(document, "trace")));

    private TraceReference BindTrace(JsonObject document) => new(
        BindArtifact(RequiredObject(document, "source")),
        RequiredString(document, "pointer"),
        RequiredString(document, "claimKind"));

    private static JsonObject RequiredObject(JsonObject parent, string name) =>
        parent[name] as JsonObject ?? throw new InvalidDataException($"{name} must be an object.");

    private static JsonArray RequiredArray(JsonObject parent, string name) =>
        parent[name] as JsonArray ?? throw new InvalidDataException($"{name} must be an array.");

    private static string RequiredString(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidDataException($"{name} must be a non-empty string.");

    private static DateTimeOffset ParseInstant(JsonObject parent, string name) =>
        DateTimeOffset.ParseExact(RequiredString(parent, name), "yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);

    private static T ParseEnum<T>(string value)
        where T : struct, Enum
    {
        string normalized = value.Replace("-", string.Empty, StringComparison.Ordinal);
        return Enum.TryParse(normalized, true, out T result)
            ? result
            : throw new InvalidDataException($"Unsupported {typeof(T).Name} value: {value}");
    }
}
