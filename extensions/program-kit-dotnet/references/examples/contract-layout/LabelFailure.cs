namespace ProgramKit.Examples.Contracts;

/// <summary>Identifies a stable validation failure without private input.</summary>
/// <param name="Code">The public stable failure code.</param>
public sealed record LabelFailure(string Code);
