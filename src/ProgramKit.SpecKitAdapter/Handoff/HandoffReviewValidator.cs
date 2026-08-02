using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Handoff;

public static class HandoffReviewValidator
{
    public static TraceResolution Validate(string workspaceRoot, BoundHandoff handoff, JsonObject review)
    {
        AdapterSchemaValidator.Validate("handoff-review.schema.json", review);
        if (review["decision"]!.GetValue<string>() != "approved") throw new InvalidDataException("The handoff review is not approved.");
        string reviewedDigest = review["handoff"]?["digest"]?.GetValue<string>() ?? throw new InvalidDataException("The review has no handoff digest.");
        if (!string.Equals(reviewedDigest, handoff.Digest, StringComparison.Ordinal)) throw new InvalidDataException("The handoff changed after review.");
        string[] reviewedFields = review["reviewedFields"]!.AsArray().Select(static node => node!.GetValue<string>()).ToArray();
        if (handoff.TraceTargets.Except(reviewedFields, StringComparer.Ordinal).Any()) throw new InvalidDataException("The review does not cover every traced output field.");
        JsonObject digestMaterial = (JsonObject)review.DeepClone();
        string declaredDigest = digestMaterial["digest"]!.GetValue<string>();
        digestMaterial.Remove("digest");
        if (!string.Equals(declaredDigest, CanonicalDocument.Digest(digestMaterial), StringComparison.Ordinal)) throw new InvalidDataException("The review digest is not exact.");
        return TraceResolver.Validate(workspaceRoot, handoff);
    }
}
