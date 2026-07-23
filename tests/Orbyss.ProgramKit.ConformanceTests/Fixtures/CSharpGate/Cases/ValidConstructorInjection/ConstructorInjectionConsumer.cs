namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidConstructorInjection;

internal sealed class ConstructorInjectionConsumer
{
    private readonly IConstructorValidator validator;

    public ConstructorInjectionConsumer(IConstructorValidator validator)
    {
        this.validator = validator;
    }

    public bool Validate() => validator.Validate();
}
