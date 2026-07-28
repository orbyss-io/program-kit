namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestRunRequest
{
    public JTestRunRequest(string suite, int maximumParallelism)
    {
        Suite = suite;
        MaximumParallelism = maximumParallelism;
    }

    public string Suite { get; }

    public int MaximumParallelism { get; }
}
