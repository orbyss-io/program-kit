namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Finite System.Diagnostics.ActivityKind selection.</summary>
public enum DotNetActivityKind
{
    /// <summary>An in-process operation.</summary>
    Internal,
    /// <summary>An inbound server operation.</summary>
    Server,
    /// <summary>An outbound client operation.</summary>
    Client,
    /// <summary>A message producer operation.</summary>
    Producer,
    /// <summary>A message consumer operation.</summary>
    Consumer,
}
