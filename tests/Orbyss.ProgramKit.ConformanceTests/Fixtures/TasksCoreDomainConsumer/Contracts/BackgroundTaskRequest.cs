namespace Orbyss.ProgramKit.TasksCoreDomainConsumerFixture.Contracts;

/// <summary>Consumer-owned request model for volatile background work.</summary>
public sealed record BackgroundTaskRequest(string Subject);
