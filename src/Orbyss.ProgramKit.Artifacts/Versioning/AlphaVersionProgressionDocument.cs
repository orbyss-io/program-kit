namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Binds one explicit proposal to one exact replaceable alpha policy.</summary>
/// <param name="Policy">Exact selected progression policy.</param>
/// <param name="Proposal">Explicit caller-selected proposal.</param>
public sealed record AlphaVersionProgressionDocument(
    AlphaVersionProgressionPolicy Policy,
    AlphaVersionProgressionProposal Proposal);
