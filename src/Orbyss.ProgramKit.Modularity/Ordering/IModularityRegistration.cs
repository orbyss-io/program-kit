namespace Orbyss.ProgramKit.Modularity.Ordering;

/// <summary>Exposes stable metadata shared by all explicit modularity registrations.</summary>
public interface IModularityRegistration
{
    /// <summary>Gets the exact identity, owner, and ordering metadata.</summary>
    ModularityRegistrationDescriptor Descriptor { get; }
}
