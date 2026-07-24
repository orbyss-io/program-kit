namespace Orbyss.ProgramKit.CommandLine.Commands.Parsing;

/// <summary>Parses OS token arrays against the frozen command grammar.</summary>
public interface ICommandParser
{
    /// <summary>Parses one complete invocation or throws an expected grammar failure.</summary>
    CommandInvocation Parse(IReadOnlyList<string> tokens);
}
