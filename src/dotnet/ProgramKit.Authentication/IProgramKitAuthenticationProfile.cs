namespace ProgramKit.Authentication;

/// <summary>Identifies one concrete Program Kit authentication profile in a shell.</summary>
public interface IProgramKitAuthenticationProfile
{
    /// <summary>Gets the stable profile identity.</summary>
    string Name { get; }
}
