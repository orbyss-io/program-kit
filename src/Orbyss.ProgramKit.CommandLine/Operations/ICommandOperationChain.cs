namespace Orbyss.ProgramKit.CommandLine.Operations;

/// <summary>One explicit link in an exact command-operation registration chain.</summary>
public interface ICommandOperationChain
{
    /// <summary>Gets whether this chain contains the exact command key.</summary>
    bool Contains(string commandKey);

    /// <summary>Resolves one exact command key, if present.</summary>
    ICommandOperation? TryResolve(string commandKey);
}
