namespace Orbyss.ProgramKit.DevContainers.Contracts.Ports;

/// <summary>One explicit forwarded TCP port and non-sensitive display label.</summary>
public sealed record DevContainerForwardedPort(int Port, string Label);
