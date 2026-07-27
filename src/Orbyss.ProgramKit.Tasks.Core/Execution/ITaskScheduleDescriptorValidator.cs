namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>
/// Validates one typed schedule descriptor before scheduler activation.
/// </summary>
/// <typeparam name="TDescriptor">The typed schedule descriptor model.</typeparam>
public interface ITaskScheduleDescriptorValidator<TDescriptor>
    where TDescriptor : notnull
{
    /// <summary>Validates the selected descriptor and ambient provider evidence.</summary>
    ValueTask ValidateAsync(
        TDescriptor descriptor,
        CancellationToken cancellationToken);
}
