namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>
/// Marks a pure occurrence calculator that cannot calculate its next firing
/// until the previously bound task instance has reached a terminal state.
/// </summary>
/// <typeparam name="TDescriptor">The typed schedule descriptor model.</typeparam>
public interface ITaskTerminalCompletionOccurrenceCalculator<TDescriptor> :
    ITaskOccurrenceCalculator<TDescriptor>
    where TDescriptor : notnull;
