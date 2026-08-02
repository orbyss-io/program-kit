using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.SessionIntegration.Definitions;

public static class CanonicalSessionGuidance
{
    private static readonly byte[] GuidanceBytes = SessionIntegrationDefinitionLoader.ReadEmbeddedGuidance();

    public static CanonicalSessionIntegrationDefinition Definition { get; } =
        new SessionIntegrationDefinitionLoader().LoadEmbedded();

    public static string GuidanceText { get; } = Encoding.UTF8.GetString(GuidanceBytes);

    public static IReadOnlyList<string> WorkflowSteps { get; } = GuidanceText
        .Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
        .Where(static line =>
        {
            int separator = line.IndexOf(". ", StringComparison.Ordinal);
            return separator > 0 && line[..separator].All(static character => char.IsAsciiDigit(character));
        })
        .Select(static line => line[(line.IndexOf(". ", StringComparison.Ordinal) + 2)..])
        .ToArray();
}
