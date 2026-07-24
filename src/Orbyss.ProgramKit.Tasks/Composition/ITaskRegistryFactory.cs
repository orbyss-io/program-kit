using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Composition;

/// <summary>Creates one fail-closed immutable task registry.</summary>
public interface ITaskRegistryFactory
{
    /// <summary>Validates, orders, and freezes a finite registration set.</summary>
    ITaskRegistry Create(TaskRegistrationSet registrations);
}
