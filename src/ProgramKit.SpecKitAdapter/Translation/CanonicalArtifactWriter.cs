using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Translation;

public static class CanonicalArtifactWriter
{
    public static IReadOnlyDictionary<string, byte[]> Materialize(IReadOnlyDictionary<string, JsonObject> documents)
    {
        LogicalPathPolicy.ValidateDistinct(documents.Keys);
        return documents.OrderBy(static item => item.Key, StringComparer.Ordinal)
            .ToDictionary(static item => item.Key, static item => CanonicalDocument.Encode(item.Value), StringComparer.Ordinal);
    }
}
