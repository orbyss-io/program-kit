namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.PrimaryStructCapture;

internal struct PrimaryStructCapture(IJobValidator validator)
{
    internal bool Validate() => validator.Validate();
}
