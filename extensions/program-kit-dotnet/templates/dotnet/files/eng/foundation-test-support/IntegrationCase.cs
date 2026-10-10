namespace ProgramKit.Foundation.TestSupport;

/// <summary>A named owner-supplied behavior check, never a claim inferred from an exit code.</summary>
public sealed record IntegrationCase(string Name, Func<CancellationToken, Task> Execute);
