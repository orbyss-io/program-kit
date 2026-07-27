namespace Orbyss.ProgramKit.TasksCoreDomainConsumerFixture.Contracts;

/// <summary>Consumer-owned request model for immediate work.</summary>
public sealed record ImmediateTaskRequest(string Subject);
