using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>Identifies the exact source of authority asserted by a supplied human decision.</summary>
public sealed record AuthorityReference(
    string Kind,
    ArtifactReference Source,
    string JsonPointer,
    ProgramKitIdentifier OwnerId);
