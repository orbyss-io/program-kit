namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.MutablePrimaryConstructorCapture;

internal sealed class MutablePrimaryConstructorCapture(
    IPrimaryValidator validator)
{
    internal bool Validate() => validator.Validate();

    internal void Replace(IPrimaryValidator replacement)
    {
        validator = replacement;
    }
}
