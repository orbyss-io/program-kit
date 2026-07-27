using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Configuration;

[TestClass]
public sealed class DotNetOptionsRuntimeBehaviorTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public void FixedSnapshotAndMonitorHaveTheirDocumentedLifetimes()
    {
        var configuration = Configuration();
        using var provider = Services(configuration).BuildServiceProvider();
        var fixedOptions = provider.GetRequiredService<IOptions<ReloadableOptions>>();
        var monitor = provider.GetRequiredService<IOptionsMonitor<ReloadableOptions>>();
        using var firstScope = provider.CreateScope();
        var firstSnapshot = firstScope.ServiceProvider
            .GetRequiredService<IOptionsSnapshot<ReloadableOptions>>();

        Assert.AreEqual(1, fixedOptions.Value.Count);
        Assert.AreEqual(1, monitor.Get("named").Count);
        Assert.AreEqual(1, firstSnapshot.Get("named").Count);

        configuration["Sample:Count"] = "2";
        configuration.Reload();

        Assert.AreEqual(1, fixedOptions.Value.Count);
        Assert.AreEqual(2, monitor.Get("named").Count);
        Assert.AreEqual(1, firstSnapshot.Get("named").Count);
        using var secondScope = provider.CreateScope();
        var secondSnapshot = secondScope.ServiceProvider
            .GetRequiredService<IOptionsSnapshot<ReloadableOptions>>();
        Assert.AreEqual(2, secondSnapshot.Get("named").Count);
    }

    [TestMethod]
    public void LaterConfigurationSourceWinsForTheSameKey()
    {
        ConfigurationBuilder builder = new();
        builder.AddInMemoryCollection(
            new Dictionary<string, string?>
            {
                ["Sample:Count"] = "1",
            });
        builder.AddInMemoryCollection(
            new Dictionary<string, string?>
            {
                ["Sample:Count"] = "2",
            });
        var configuration = builder.Build();
        using var provider = Services(configuration).BuildServiceProvider();

        var options = provider
            .GetRequiredService<IOptions<ReloadableOptions>>();

        Assert.AreEqual(2, options.Value.Count);
    }

    [TestMethod]
    public void InvalidReloadIsRejectedWithoutClaimingLastKnownGoodRetention()
    {
        var configuration = Configuration();
        using var provider = Services(configuration).BuildServiceProvider();
        var monitor = provider.GetRequiredService<IOptionsMonitor<ReloadableOptions>>();
        var successfulNotifications = 0;
        using var subscription = monitor.OnChange((_, _) =>
            successfulNotifications++);
        Assert.AreEqual(1, monitor.Get("named").Count);

        configuration["Sample:Count"] = "-1";
        var reloadException = Assert.ThrowsExactly<AggregateException>(
            configuration.Reload);
        Assert.IsNotEmpty(reloadException.InnerExceptions);
        Assert.IsTrue(reloadException.InnerExceptions.All(static exception =>
            exception is OptionsValidationException));
        Assert.AreEqual(0, successfulNotifications);
        Assert.ThrowsExactly<OptionsValidationException>(
            () => monitor.Get("named"));

        configuration["Sample:Count"] = "3";
        configuration.Reload();
        Assert.AreEqual(3, monitor.Get("named").Count);
        Assert.AreEqual(2, successfulNotifications);
    }

    [TestMethod]
    public void DisposedMonitorSubscriptionReceivesNoFurtherChanges()
    {
        var configuration = Configuration();
        using var provider = Services(configuration).BuildServiceProvider();
        var monitor = provider.GetRequiredService<IOptionsMonitor<ReloadableOptions>>();
        var notifications = 0;
        var subscription = monitor.OnChange((_, _) => notifications++) ??
            throw new InvalidOperationException(
                "The monitor did not return a subscription.");

        subscription.Dispose();
        configuration["Sample:Count"] = "2";
        configuration.Reload();

        Assert.AreEqual(0, notifications);
        Assert.AreEqual(2, monitor.Get("named").Count);
    }

    [TestMethod]
    public async Task RequiredInvalidOptionsFailHostStartup()
    {
        var configuration = Configuration("-1");
        var application = Host.CreateApplicationBuilder();
        application.Logging.ClearProviders();
        application.Configuration.Sources.Clear();
        application.Configuration.AddConfiguration(configuration);
        application.Services
            .AddOptions<ReloadableOptions>("named")
            .Bind(application.Configuration.GetRequiredSection("Sample"))
            .Validate(
                static options => options.Count > 0,
                "Count must be positive.")
            .ValidateOnStart();
        using var host = application.Build();

        await Assert.ThrowsExactlyAsync<OptionsValidationException>(
            async () => await host.StartAsync(TestContext.CancellationToken));
    }

    [TestMethod]
    public void RequiredProviderFailureIsNotSilentlyDowngraded()
    {
        var missingPath = Path.Combine(
            TestContext.TestRunDirectory!,
            string.Concat(
                "missing-",
                Guid.NewGuid().ToString("N"),
                ".json"));
        ConfigurationBuilder requiredBuilder = new();
        requiredBuilder.AddJsonFile(
            missingPath,
            optional: false,
            reloadOnChange: false);

        Assert.ThrowsExactly<FileNotFoundException>(
            requiredBuilder.Build);

        ConfigurationBuilder optionalBuilder = new();
        optionalBuilder.AddJsonFile(
            missingPath,
            optional: true,
            reloadOnChange: false);
        var optionalConfiguration = optionalBuilder.Build();
        Assert.IsNull(optionalConfiguration["Sample:Count"]);
    }

    private static IConfigurationRoot Configuration(string count = "1")
    {
        ConfigurationBuilder builder = new();
        builder.AddInMemoryCollection(
            new Dictionary<string, string?>
            {
                ["Sample:Count"] = count,
            });
        return builder.Build();
    }

    private static ServiceCollection Services(IConfiguration configuration)
    {
        var services = new ServiceCollection();
        services
            .AddOptions<ReloadableOptions>()
            .Bind(configuration.GetRequiredSection("Sample"))
            .Validate(
                static options => options.Count > 0,
                "Count must be positive.");
        services
            .AddOptions<ReloadableOptions>("named")
            .Bind(configuration.GetRequiredSection("Sample"))
            .Validate(
                static options => options.Count > 0,
                "Count must be positive.");
        return services;
    }
}
