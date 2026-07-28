namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestDescribeRequest
{
    public JTestDescribeRequest(string suite)
    {
        Suite = suite;
    }

    public string Suite { get; }
}
