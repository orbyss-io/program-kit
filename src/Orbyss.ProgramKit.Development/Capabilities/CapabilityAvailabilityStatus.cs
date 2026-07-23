namespace Orbyss.ProgramKit.Development.Capabilities;

/// <summary>Identifies whether a human-session capability is registered for use.</summary>
public enum CapabilityAvailabilityStatus
{
    /// <summary>The capability is registered and available to the human session.</summary>
    Available,
    /// <summary>The capability is not available to the human session.</summary>
    Unavailable,
}
