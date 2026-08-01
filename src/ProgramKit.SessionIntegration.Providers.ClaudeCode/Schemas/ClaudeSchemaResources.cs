using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Schemas;

public static class ClaudeSchemaResources
{
    public const string MachineReviewId = "https://schemas.program-kit.dev/v1/claude-code-machine-review.schema.json";
    private const string ResourceSuffix = ".Schemas.isolated-machine-review.schema.json";

    public static string ReadMachineReview()
    {
        Assembly assembly = typeof(ClaudeSchemaResources).Assembly;
        string name = assembly.GetManifestResourceNames().Single(item => item.EndsWith(ResourceSuffix, StringComparison.Ordinal));
        using Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidOperationException("The embedded Claude machine-review schema is missing.");
        using StreamReader reader = new(stream, new UTF8Encoding(false), detectEncodingFromByteOrderMarks: true);
        return reader.ReadToEnd();
    }
}
