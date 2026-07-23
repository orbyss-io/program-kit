using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Diagnostics;

/// <summary>Defines one stable diagnostic family independently of an occurrence.</summary>
/// <param name="Id">The stable diagnostic identifier.</param>
/// <param name="DefaultSeverity">The default severity.</param>
/// <param name="Title">The stable culture-invariant title.</param>
public sealed record ProgramKitDiagnosticDefinition(
    string Id,
    ProgramKitDiagnosticSeverity DefaultSeverity,
    string Title);
