namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureValidationResult
{
    public MetadataFixtureValidationResult(
        bool isValid,
        IReadOnlyList<string> messages)
    {
        IsValid = isValid;
        Messages = messages;
    }

    public bool IsValid { get; }

    public IReadOnlyList<string> Messages { get; }
}
