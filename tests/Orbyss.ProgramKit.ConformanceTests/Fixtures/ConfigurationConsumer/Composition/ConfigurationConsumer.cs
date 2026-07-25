using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Orbyss.ProgramKit.ConfigurationConsumerFixture.Configuration;

namespace Orbyss.ProgramKit.ConfigurationConsumerFixture.Composition;

/// <summary>Isolated generated-runtime composition proving the configuration closure.</summary>
public static class ConfigurationConsumer
{
    /// <summary>Binds and validates generated Options without any Program Kit runtime assembly.</summary>
    public static bool Validate()
    {
        ConfigurationBuilder configurationBuilder = new();
        configurationBuilder.AddInMemoryCollection(
            new Dictionary<string, string?>
            {
                ["Consumer:Count"] = "3",
            });
        var configuration = configurationBuilder.Build();
        var services = new ServiceCollection();
        services.AddSingleton<
            IValidateOptions<GeneratedConsumerOptions>,
            GeneratedConsumerOptionsValidator>();
        services
            .AddOptions<GeneratedConsumerOptions>()
            .Bind(configuration.GetRequiredSection("Consumer"))
            .ValidateOnStart();
        using var provider = services.BuildServiceProvider();
        var options = provider
            .GetRequiredService<IOptions<GeneratedConsumerOptions>>();
        if (options.Value.Count != 3)
        {
            return false;
        }

        configuration["Consumer:Count"] = "30";
        configuration.Reload();
        return ThrowsGeneratedValidation(provider);
    }

    private static bool ThrowsGeneratedValidation(IServiceProvider provider)
    {
        try
        {
            using var scope = provider.CreateScope();
            _ = scope.ServiceProvider
                .GetRequiredService<IOptionsSnapshot<GeneratedConsumerOptions>>()
                .Value;
            return false;
        }
        catch (OptionsValidationException)
        {
            return true;
        }
    }
}
