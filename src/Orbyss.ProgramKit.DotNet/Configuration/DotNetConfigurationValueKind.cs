namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Closed configuration scalar types supported by deterministic Options generation.</summary>
public enum DotNetConfigurationValueKind
{
    /// <summary>String value.</summary>
    Text,
    /// <summary>Boolean value.</summary>
    Boolean,
    /// <summary>32-bit integer value.</summary>
    WholeNumber32,
    /// <summary>64-bit integer value.</summary>
    WholeNumber64,
    /// <summary>Decimal value.</summary>
    DecimalNumber,
    /// <summary>Double-precision value.</summary>
    FloatingPoint,
    /// <summary>Absolute URI value.</summary>
    AbsoluteUri,
    /// <summary>Time-span value.</summary>
    Duration,
}
