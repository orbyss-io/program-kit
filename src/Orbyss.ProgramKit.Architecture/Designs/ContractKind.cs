using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>The role of a public contract.</summary>
public enum ContractKind
{
    /// <summary>A request accepted by a caller-visible operation.</summary>
    Request,

    /// <summary>A successful result produced by an operation.</summary>
    Response,

    /// <summary>A stable failure contract.</summary>
    Failure,

    /// <summary>An event-like fact.</summary>
    Contribution,

    /// <summary>A configuration contract.</summary>
    Configuration,

    /// <summary>A public service interface.</summary>
    Service,

    /// <summary>A persisted or exchanged value contract.</summary>
    Value
}
