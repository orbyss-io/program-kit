namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureRequest
{
    public MetadataFixtureRequest(
        string target,
        int count,
        bool force,
        bool confirm)
    {
        Target = target;
        Count = count;
        Force = force;
        Confirm = confirm;
    }

    public string Target { get; }

    public int Count { get; }

    public bool Force { get; }

    public bool Confirm { get; }
}
