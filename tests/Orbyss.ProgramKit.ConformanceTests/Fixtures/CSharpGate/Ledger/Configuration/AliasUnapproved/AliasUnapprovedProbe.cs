using Alias = System.Diagnostics.CodeAnalysis.SuppressMessageAttribute;

[assembly: Alias(
    "Compiler",
    "CS1591",
    Justification = "Negative semantic alias suppression fixture.")]

namespace Orbyss.ProgramKit.LedgerProbe.Configuration.AliasUnapproved;

public sealed record AliasUnapprovedProbe;
