namespace GeneratedHost.Hosting;

internal sealed class FileFixtureLifecycleRecorder :
    IFixtureLifecycleRecorder
{
    public void Record(string value)
    {
        var path = Environment.GetEnvironmentVariable(
            "PROGRAM_KIT_CONSOLE_FIXTURE_LIFECYCLE");
        if (string.IsNullOrWhiteSpace(path))
        {
            throw new InvalidOperationException(
                "The fixture lifecycle path is required.");
        }

        File.AppendAllText(
            path,
            string.Concat(value, Environment.NewLine));
    }
}
