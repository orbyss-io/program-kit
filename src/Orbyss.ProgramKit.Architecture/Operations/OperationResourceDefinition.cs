using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>One resource and its ownership lifecycle.</summary>
public sealed record OperationResourceDefinition(
    string Resource,
    ProgramKitIdentifier OwnerId,
    string Acquisition,
    string Release,
    bool OwnershipTransfers);
