using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static class ContinuationBuilder
{
    public static Continuation ForMissing(string requestDigest, IEnumerable<string> missing)
    {
        MissingInput[] inputs = missing.Distinct(StringComparer.Ordinal).OrderBy(static item => item, StringComparer.Ordinal).Select(identity => new MissingInput(
            identity,
            "contract-field",
            identity.StartsWith("authority", StringComparison.Ordinal) ? "human-approval" : "consumer-intent",
            ProtocolIdentities.Rule("request.missing-input"))).ToArray();
        JsonObject identityDocument = new()
        {
            ["schema"] = "program-kit.continuation/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["requestDigest"] = requestDigest,
            ["missingInputs"] = new JsonArray(inputs.Select(static item => JsonValue.Create(item.Identity)).ToArray()),
        };
        string empty = Digests.Sha256(Array.Empty<byte>());
        return new Continuation(
            "program-kit.continuation/v1",
            CanonicalJson.Profile,
            requestDigest,
            inputs,
            new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal),
            inputs.Select(static item => item.RequiredAuthority).Distinct(StringComparer.Ordinal).OrderBy(static item => item, StringComparer.Ordinal).ToArray(),
            empty,
            empty,
            CanonicalJson.Digest(identityDocument));
    }
}
