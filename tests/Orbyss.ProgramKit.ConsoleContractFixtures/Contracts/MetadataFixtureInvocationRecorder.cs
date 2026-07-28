namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public static class MetadataFixtureInvocationRecorder
{
    private static int handlerCalls;
    private static int validatorCalls;

    public static int HandlerCalls =>
        Volatile.Read(ref handlerCalls);

    public static int ValidatorCalls =>
        Volatile.Read(ref validatorCalls);

    public static bool ValidatorIsValid { get; set; } = true;

    public static IReadOnlyList<string> ValidatorMessages { get; set; } = [];

    public static bool HandlerObservedCancellation { get; private set; }

    public static void Reset()
    {
        Interlocked.Exchange(ref handlerCalls, 0);
        Interlocked.Exchange(ref validatorCalls, 0);
        ValidatorIsValid = true;
        ValidatorMessages = [];
        HandlerObservedCancellation = false;
    }

    internal static void RecordHandler(
        CancellationToken cancellationToken)
    {
        Interlocked.Increment(ref handlerCalls);
        HandlerObservedCancellation =
            cancellationToken.CanBeCanceled;
    }

    internal static void RecordValidator()
    {
        Interlocked.Increment(ref validatorCalls);
    }
}
