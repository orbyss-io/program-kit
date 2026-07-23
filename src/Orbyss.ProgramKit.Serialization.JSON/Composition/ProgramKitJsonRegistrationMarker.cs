using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

internal sealed class ProgramKitJsonRegistrationMarker
{
    internal ProgramKitJsonRegistrationMarker(
        IServiceCollection services,
        IProgramKitJsonBuilder builder,
        Func<IServiceProvider, IProgramKitJsonRegistry> registryResolver)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(builder);
        ArgumentNullException.ThrowIfNull(registryResolver);
        Services = services;
        Builder = builder;
        RegistryResolver = registryResolver;
    }

    internal IServiceCollection Services { get; }

    internal IProgramKitJsonBuilder Builder { get; }

    internal Func<IServiceProvider, IProgramKitJsonRegistry> RegistryResolver
    {
        get;
    }
}
