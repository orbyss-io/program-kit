using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Reconciles one .NET binding document with one Open Console document.</summary>
public interface IDotNetConsoleBindingValidator
{
    /// <summary>Validates structure and exact one-to-one command mappings.</summary>
    ProgramKitValidationResult Validate(
        DotNetConsoleBindingDocument binding,
        OpenConsoleDocument openConsole);
}
