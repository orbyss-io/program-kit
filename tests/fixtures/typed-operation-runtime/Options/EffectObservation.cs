namespace ProgramKit.Examples.TypedOperation.OptionsProbe;

/// <summary>Records protected work when the native later-phase initializer actually executes.</summary>
internal sealed class EffectObservation
{
    /// <summary>Counts effect-phase executions, independently from initializer object construction.</summary>
    internal int Starts { get; set; }
}
