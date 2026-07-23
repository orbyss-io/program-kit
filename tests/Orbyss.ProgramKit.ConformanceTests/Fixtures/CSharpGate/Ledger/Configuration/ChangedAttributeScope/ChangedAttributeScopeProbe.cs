using System.Diagnostics.CodeAnalysis;

[assembly: SuppressMessage(
    "Compiler",
    "CS1591",
    Scope = "module",
    Justification = "Negative scope-widening conformance fixture.")]

namespace Orbyss.ProgramKit.LedgerProbe.Configuration.ChangedAttributeScope;

public sealed record ChangedAttributeScopeProbe;
