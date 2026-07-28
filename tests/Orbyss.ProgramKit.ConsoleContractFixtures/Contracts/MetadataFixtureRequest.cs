namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureRequest
{
    public MetadataFixtureRequest(
        string target,
        int count,
        bool force,
        bool confirm,
        long total,
        decimal ratio,
        Guid correlation,
        DateTimeOffset at,
        System.Collections.Immutable.ImmutableArray<string> tags)
    {
        Target = target;
        Count = count;
        Force = force;
        Confirm = confirm;
        Total = total;
        Ratio = ratio;
        Correlation = correlation;
        At = at;
        Tags = tags;
    }

    public string Target { get; }

    public int Count { get; }

    public bool Force { get; }

    public bool Confirm { get; }

    public long Total { get; }

    public decimal Ratio { get; }

    public Guid Correlation { get; }

    public DateTimeOffset At { get; }

    public System.Collections.Immutable.ImmutableArray<string> Tags { get; }
}
