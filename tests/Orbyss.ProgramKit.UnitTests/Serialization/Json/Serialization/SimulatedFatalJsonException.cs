namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed class SimulatedFatalJsonException : OutOfMemoryException
{
    internal SimulatedFatalJsonException(string message)
        : base(message)
    {
    }
}
