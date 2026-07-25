namespace Orbyss.ProgramKit.DotNet.Operations.TransportFailures;

/// <summary>Behavior for request cancellation caused by a disconnected client.</summary>
public enum DotNetClientDisconnectDisposition
{
    /// <summary>Abort without manufacturing an HTTP failure response.</summary>
    AbortWithoutResponse,
}
