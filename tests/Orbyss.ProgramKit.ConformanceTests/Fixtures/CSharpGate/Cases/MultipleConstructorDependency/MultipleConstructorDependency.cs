namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.MultipleConstructorDependency;

internal sealed class MultipleConstructorDependency
{
    private readonly IMultipleConstructorValidator? validator;

    internal MultipleConstructorDependency(
        IMultipleConstructorValidator validator)
    {
        this.validator = validator;
    }

    internal MultipleConstructorDependency()
    {
    }

    internal bool Validate() => validator?.Validate() ?? false;
}
