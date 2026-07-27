using System.Globalization;

namespace GeneratedHost.Commands;

internal sealed class FixtureExitCodePolicy : IFixtureExitCodePolicy
{
    public int Resolve(string value) =>
        int.TryParse(
            value,
            NumberStyles.Integer,
            CultureInfo.InvariantCulture,
            out var exitCode)
            ? exitCode
            : throw new InvalidOperationException(
                "The parsed fixture exit code was not an integer.");
}
