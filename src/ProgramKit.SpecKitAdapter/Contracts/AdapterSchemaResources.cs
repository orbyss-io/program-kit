using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.SpecKitAdapter.Contracts;

public static class AdapterSchemaResources
{
    public static IReadOnlyDictionary<string, string> ReadAll()
    {
        Assembly assembly = typeof(AdapterSchemaResources).Assembly;
        return assembly.GetManifestResourceNames()
            .Where(static name => name.Contains(".Schemas.", StringComparison.Ordinal) && name.EndsWith(".schema.json", StringComparison.Ordinal))
            .OrderBy(static name => name, StringComparer.Ordinal)
            .ToDictionary(
                static name => name[(name.LastIndexOf('.', name.Length - ".schema.json".Length - 1) + 1)..],
                name =>
                {
                    using Stream stream = assembly.GetManifestResourceStream(name)
                        ?? throw new InvalidOperationException($"Missing schema resource: {name}");
                    using StreamReader reader = new(stream);
                    return reader.ReadToEnd();
                },
                StringComparer.Ordinal);
    }

    public static string ReadByIdentity(string identity) => ReadAll().Values.Single(content =>
        string.Equals(JsonNode.Parse(content)?["$id"]?.GetValue<string>(), identity, StringComparison.Ordinal));
}
