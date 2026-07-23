using System.Diagnostics.CodeAnalysis;

[assembly: SuppressMessage(
    checkId: "CS1591",
    category: "Compiler",
    Justification = "Exact reordered named-argument conformance suppression.")]

namespace Orbyss.ProgramKit.LedgerProbe.Configuration.ApprovedNamedArguments;

public sealed record ApprovedNamedArgumentsProbe;
