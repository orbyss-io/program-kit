namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestValidateRequest
{
    public JTestValidateRequest(string path)
    {
        Path = path;
    }

    public string Path { get; }
}
