namespace Orbyss.ProgramKit.TasksCoreDomainConsumerFixture.Contracts;

/// <summary>Consumer-owned request model for scheduled work.</summary>
public sealed record ScheduledTaskRequest(string Subject);
