using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Handoff;

public sealed record BoundHandoff(JsonObject Document, string Digest, IReadOnlyList<string> TraceTargets);

public sealed class HandoffBinder
{
    private static readonly string[] RequiredTraceTargets =
    {
        "/feature",
        "/intentOwner",
        "/applicability",
        "/effectiveSelection",
        "/definitionFamily",
        "/definition",
        "/implementation",
        "/evaluationContext",
        "/requestedOperation",
        "/maximumEffect",
        "/ownership",
        "/deferred",
        "/excluded",
    };

    private static readonly HashSet<string> ForbiddenNames = new(StringComparer.OrdinalIgnoreCase)
    {
        "grant", "authorityGrant", "issuer", "credential", "secret", "prompt", "transcript", "shellCommand", "commandLine",
    };

    public BoundHandoff Bind(JsonObject handoff, bool requireComplete)
    {
        AdapterSchemaValidator.Validate("handoff.schema.json", handoff);
        RejectForbidden(handoff);
        string applicability = handoff["applicability"]!.GetValue<string>();
        if (applicability == "applicable" && handoff["effectiveSelection"] is not JsonObject)
            throw new InvalidDataException("An applicable handoff requires one exact effective selection.");
        if (requireComplete && (handoff["unresolved"]!.AsArray().Count > 0 || handoff["unsupported"]!.AsArray().Count > 0))
            throw new InvalidDataException("Translation requires empty unresolved and unsupported lists.");
        string[] traceTargets = handoff["trace"]!.AsArray().OfType<JsonObject>()
            .Select(static trace => trace["targetPointer"]?.GetValue<string>() ?? throw new InvalidDataException("Every trace requires a targetPointer."))
            .ToArray();
        if (traceTargets.Distinct(StringComparer.Ordinal).Count() != traceTargets.Length)
            throw new InvalidDataException("Every traced output field must have exactly one source.");
        if (requireComplete)
        {
            IEnumerable<string> required = handoff.ContainsKey("constructionMode")
                ? RequiredTraceTargets.Append("/constructionMode")
                : RequiredTraceTargets;
            string[] missing = required.Except(traceTargets, StringComparer.Ordinal).OrderBy(static value => value, StringComparer.Ordinal).ToArray();
            string[] unexpected = traceTargets.Except(required, StringComparer.Ordinal).OrderBy(static value => value, StringComparer.Ordinal).ToArray();
            if (missing.Length > 0 || unexpected.Length > 0)
                throw new InvalidDataException("A complete handoff requires exactly one trace for every identity or output-affecting field.");
        }
        return new BoundHandoff((JsonObject)handoff.DeepClone(), CanonicalDocument.Digest(handoff), traceTargets);
    }

    private static void RejectForbidden(JsonNode node)
    {
        if (node is JsonObject document)
        {
            foreach ((string name, JsonNode? value) in document)
            {
                if (ForbiddenNames.Contains(name)) throw new InvalidDataException("The handoff contains a forbidden authority, secret, transcript, or executable field.");
                if (value is not null) RejectForbidden(value);
            }
        }
        else if (node is JsonArray array)
        {
            foreach (JsonNode? value in array) if (value is not null) RejectForbidden(value);
        }
    }
}
