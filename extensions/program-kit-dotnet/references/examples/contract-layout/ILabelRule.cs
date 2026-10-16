namespace ProgramKit.Examples.Contracts;

/// <summary>Decides whether an input label satisfies its declared rule.</summary>
public interface ILabelRule
{
    /// <summary>Returns whether the supplied value satisfies the rule.</summary>
    /// <param name="value">The unmodified value to inspect.</param>
    /// <returns>Whether the rule admits the value.</returns>
    bool IsAdmitted(string value);
}
