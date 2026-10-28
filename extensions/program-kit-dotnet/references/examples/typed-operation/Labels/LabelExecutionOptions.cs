using System;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Owns the sample's restart-bound execution safeguard; no default is chosen by semantic Core.</summary>
public sealed class LabelExecutionOptions
{
    /// <summary>Complete write-and-observe or read budget; the thirty-second sample default is an I/O safeguard.</summary>
    public TimeSpan Timeout { get; set; } = TimeSpan.FromSeconds(30);
}
