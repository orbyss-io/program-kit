using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>
/// Question 9: redacted, externalized, or ephemeral data treatment.
/// </summary>
public sealed record DataHandlingAnswer(
    bool ContainsSensitiveData,
    string RedactionPolicy,
    string ExternalizationPolicy,
    bool ContainsEphemeralData,
    string EphemeralDataPolicy);
