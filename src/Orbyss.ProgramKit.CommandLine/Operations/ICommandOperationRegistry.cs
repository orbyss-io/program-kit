namespace Orbyss.ProgramKit.CommandLine.Operations;

/// <summary>Resolves exact command operation registrations without discovery.</summary>
public interface ICommandOperationRegistry
{
    /// <summary>Resolves exactly one operation for the descriptor key.</summary>
    ICommandOperation Resolve(string commandKey);
}
