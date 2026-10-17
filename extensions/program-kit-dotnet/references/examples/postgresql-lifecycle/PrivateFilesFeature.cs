using CShells;
using CShells.Features;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Admits the actual owner configuration; never supplies an alternate key.</summary>
[ShellFeature("ProgramKit.PrivateFilesBinding")]
public sealed class PrivateFilesFeature(ShellSettings settings) : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        var options = settings.GetConfigurationRoot().GetSection("EvidenceFiles").Get<PrivateFilesOptions>();
        if (options is null || string.IsNullOrWhiteSpace(options.Root))
            throw new InvalidOperationException("Required provider setting EvidenceFiles:Root is missing.");
        services.AddSingleton(options);
    }
}
