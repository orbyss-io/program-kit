namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ServiceConstruction;

public sealed class ServiceConstructionProbe
{
    public object Create()
    {
        var validator = new SampleValidator();
        return validator;
    }
}
