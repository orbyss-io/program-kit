using CShells.Features;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.Evidence;

/// <summary>Registers the owning runtime capability at request scope.</summary>
[ShellFeature("Evidence.Runtime")]
public sealed class EvidenceRuntimeFeature : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services) =>
        services.AddScoped<IEvidenceSubmissions, EvidenceSubmissions>();
}
