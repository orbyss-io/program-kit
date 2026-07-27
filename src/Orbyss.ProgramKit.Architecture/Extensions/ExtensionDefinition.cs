using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>
/// An extension point and the semantic fields required by its selected kind.
/// Fields that do not apply to the selected kind remain absent and are rejected
/// when populated, keeping the wire contract non-polymorphic and explicit.
/// </summary>
public sealed record ExtensionDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ExtensionKind Kind,
    ArtifactReference Contract,
    ExtensionSemantics Semantics);
