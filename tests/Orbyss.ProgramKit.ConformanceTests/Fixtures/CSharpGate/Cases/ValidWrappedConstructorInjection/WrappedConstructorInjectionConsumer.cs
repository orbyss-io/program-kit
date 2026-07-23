namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidWrappedConstructorInjection;

internal sealed class WrappedConstructorInjectionConsumer
{
    private readonly Func<IWrappedConstructorValidator> createValidator;

    internal WrappedConstructorInjectionConsumer(
        Func<IWrappedConstructorValidator> createValidator)
    {
        this.createValidator = createValidator;
    }

    internal bool Validate() => createValidator().Validate();
}
