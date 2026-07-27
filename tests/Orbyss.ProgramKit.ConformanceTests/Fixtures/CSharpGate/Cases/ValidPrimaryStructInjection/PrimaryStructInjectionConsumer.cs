namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidPrimaryStructInjection;

internal readonly struct PrimaryStructInjectionConsumer(
    IJobValidator validator)
{
    private readonly IJobValidator validator = validator;

    internal bool Validate() => validator.Validate();
}
