namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidPrimaryConstructorInjection;

internal sealed class PrimaryConstructorInjectionConsumer(
    IPrimaryValidator validator)
{
    private readonly IPrimaryValidator validator = validator;

    public bool Validate() => validator.Validate();
}
