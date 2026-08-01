using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

namespace Orbyss.ProgramKit.Contracts.Schemas;

public static class ContractSchemaResources
{
    public static IReadOnlyDictionary<string, string> ReadAll()
    {
        Assembly assembly = typeof(ContractSchemaResources).Assembly;
        return assembly.GetManifestResourceNames()
            .Where(static name => name.EndsWith(".schema.json", StringComparison.Ordinal))
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
}
