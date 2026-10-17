namespace ProgramKit.Examples.TypedOperation;

/// <summary>Consumer scalar options; the sample requires explicit configuration.</summary>
public sealed class LabelApiOptions
{
    /// <summary>Non-secret response prefix selected by the application's shell configuration.</summary>
    public string Prefix { get; set; } = "";
}
