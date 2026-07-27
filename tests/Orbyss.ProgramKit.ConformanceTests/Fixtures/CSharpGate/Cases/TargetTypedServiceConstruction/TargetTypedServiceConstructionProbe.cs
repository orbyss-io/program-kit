using ValidatorAlias =
    Orbyss.ProgramKit.CSharpGateProbe.Cases.TargetTypedServiceConstruction.SampleValidator;

namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.TargetTypedServiceConstruction;

public sealed class TargetTypedServiceConstructionProbe
{
    public void Construct()
    {
        SampleValidator targetTyped = new();
        targetTyped.Validate();

        var aliased = new ValidatorAlias();
        aliased.Validate();
    }
}
