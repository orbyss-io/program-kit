namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed class StubJsonCanonicalizer : IProgramKitJsonCanonicalizer
{
    private readonly CanonicalJsonValue result;

    internal StubJsonCanonicalizer(CanonicalJsonValue result)
    {
        this.result = result;
    }

    internal int CanonicalizeCallCount { get; private set; }

    internal byte[]? LastInput { get; private set; }

    internal JsonSerializationLimits? LastLimits { get; private set; }

    public CanonicalJsonValue Canonicalize(
        ReadOnlySpan<byte> utf8Json,
        JsonSerializationLimits limits)
    {
        CanonicalizeCallCount++;
        LastInput = utf8Json.ToArray();
        LastLimits = limits;
        return result;
    }

    public CanonicalJsonValue CanonicalizeNumber(double value) =>
        throw new InvalidOperationException(
            "The serializer must not canonicalize a standalone number.");
}
