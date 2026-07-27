using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.LedgerProbe.Configuration.ChangedAttributeTarget;

public sealed class ChangedAttributeTargetProbe
{
    [return: SuppressMessage(
        checkId: "CS1591",
        category: "Compiler",
        Justification = "Negative attribute-target conformance fixture.")]
    public string Read() => string.Empty;
}
