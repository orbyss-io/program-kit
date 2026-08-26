using System.Reflection;
using CShells.Features;
using Nuplane.Loading;

namespace ProgramKit.Host.Feed;

internal sealed class NuplaneAssemblyProvider(IPackageAssemblyCatalog packageAssemblyCatalog) : IFeatureAssemblyProvider
{
    public async Task<IEnumerable<Assembly>> GetAssembliesAsync(
        IServiceProvider serviceProvider,
        CancellationToken cancellationToken = default) =>
        await packageAssemblyCatalog.GetAssembliesAsync(cancellationToken).ConfigureAwait(false);
}
