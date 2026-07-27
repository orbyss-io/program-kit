using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Orbyss.ProgramKit.ConfigurationConsumerFixture.Configuration;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class ConfigurationProviderReloadConformanceTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task IsolatedGeneratedProvidersComposeAndReloadControlledFiles()
    {
        var directory = Directory.CreateTempSubdirectory(
            "program-kit-w030-provider-");
        var jsonPath = Path.Combine(directory.FullName, "appsettings.json");
        var keyPath = Path.Combine(directory.FullName, "keys");
        Directory.CreateDirectory(keyPath);
        var keyFile = Path.Combine(keyPath, "Generated__KeyValue");
        try
        {
            await File.WriteAllTextAsync(
                jsonPath,
                """{"Generated":{"JsonValue":"json-one"}}""",
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                keyFile,
                "key-one",
                TestContext.CancellationToken);
            HostApplicationBuilder builder = new(
                new HostApplicationBuilderSettings
                {
                    DisableDefaults = true,
                    EnvironmentName = Environments.Production,
                    ContentRootPath = directory.FullName,
                });
            ConfigurationProviderComposition.AddReviewedProviders(
                builder,
                ["--Generated:CommandValue=command"],
                "appsettings.json",
                keyPath);
            using var host = builder.Build();

            Assert.AreEqual(
                "json-one",
                builder.Configuration["Generated:JsonValue"]);
            Assert.AreEqual(
                "key-one",
                builder.Configuration["Generated:KeyValue"]);
            Assert.AreEqual(
                "command",
                builder.Configuration["Generated:CommandValue"]);
            Assert.AreEqual(
                "in-memory",
                builder.Configuration["Generated:PublicValue"]);
            Assert.AreEqual(
                "chained",
                builder.Configuration["Generated:ChainedValue"]);

            await ChangeAndAwaitReloadAsync(
                builder.Configuration,
                "Generated:JsonValue",
                "json-two",
                () => File.WriteAllText(
                    jsonPath,
                    """{"Generated":{"JsonValue":"json-two"}}"""),
                TestContext.CancellationToken);
            await ChangeAndAwaitReloadAsync(
                builder.Configuration,
                "Generated:KeyValue",
                "key-two",
                () => File.WriteAllText(keyFile, "key-two"),
                TestContext.CancellationToken);
        }
        finally
        {
            DeleteTemporaryDirectory(directory);
        }
    }

    private static async Task ChangeAndAwaitReloadAsync(
        IConfiguration configuration,
        string key,
        string expected,
        Action change,
        CancellationToken cancellationToken)
    {
        TaskCompletionSource reloaded = new(
            TaskCreationOptions.RunContinuationsAsynchronously);
        using var registration = configuration.GetReloadToken()
            .RegisterChangeCallback(
                static state => ((TaskCompletionSource)state!).TrySetResult(),
                reloaded);

        change();
        await reloaded.Task.WaitAsync(
            TimeSpan.FromSeconds(10),
            cancellationToken);

        Assert.AreEqual(expected, configuration[key]);
    }

    private static void DeleteTemporaryDirectory(DirectoryInfo directory)
    {
        var temporaryRoot = Path.GetFullPath(Path.GetTempPath());
        var target = Path.GetFullPath(directory.FullName);
        if (!target.StartsWith(
                temporaryRoot,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "Refusing to clean a directory outside the temporary root.");
        }

        if (directory.Exists)
        {
            directory.Delete(recursive: true);
        }
    }
}
