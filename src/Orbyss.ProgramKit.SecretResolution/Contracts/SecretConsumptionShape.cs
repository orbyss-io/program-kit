namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>How a consumer receives the selected result capability.</summary>
public enum SecretConsumptionShape
{
    /// <summary>No consumption shape was selected.</summary>
    Unspecified,
    /// <summary>The consumer receives the native typed result capability.</summary>
    NativeCapability,
    /// <summary>The consumer projects text or bytes into configuration mechanics.</summary>
    Configuration,
}
