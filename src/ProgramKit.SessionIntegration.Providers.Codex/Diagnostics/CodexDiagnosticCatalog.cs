using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;

public static class CodexDiagnosticCatalog
{
    public const string Version = "1.0.0";
    public static IReadOnlyDictionary<string, string> Entries { get; } = new ReadOnlyDictionary<string, string>(new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["orbyss.program-kit.codex/PKCDX0001"] = "The repository-skill projection could not preserve the canonical guidance boundary.",
        ["orbyss.program-kit.codex/PKCDX0002"] = "The selected provider surface revision is incompatible.",
        ["orbyss.program-kit.codex/PKCDX0003"] = "Provider-session availability could not be established and remains not-evaluated.",
    });
}
