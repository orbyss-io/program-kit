using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>An allowed or forbidden reference relation traced to an owner input.</summary>
public sealed record ReferenceRuleDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ReferenceRuleDisposition Disposition,
    string ReferencingScope,
    string ReferencedScope,
    SourceTrace OwnerInput,
    string Rationale);
