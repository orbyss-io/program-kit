using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>Explicit shell-scoped DI registration for Serialization.JSON.</summary>
public static class ProgramKitJsonServiceCollectionExtensions
{
    /// <summary>Adds one shell-scoped builder, registry, and typed serializer.</summary>
    public static IProgramKitJsonBuilder AddProgramKitJson(
        this IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        if (TryGetCompleteRegistration(services, out var existing))
        {
            return existing;
        }

        IProgramKitJsonRegistryFactory registryFactory =
            new ProgramKitJsonRegistryFactory();
        var builder = new ProgramKitJsonBuilder(registryFactory);
        Func<IServiceProvider, IProgramKitJsonRegistry> registryResolver =
            ResolveOwnedRegistry;
        var registrationMarker = new ProgramKitJsonRegistrationMarker(
            services,
            builder,
            registryResolver);
        services.AddSingleton(registrationMarker);
        services.AddSingleton<IProgramKitJsonRegistryFactory>(registryFactory);
        services.AddSingleton<IProgramKitJsonBuilder>(builder);
        services.AddSingleton(registryResolver);
        services.AddSingleton<
            IProgramKitJsonCanonicalizer,
            ProgramKitJsonCanonicalizer>();
        services.AddSingleton<IProgramKitJsonSerializer, ProgramKitJsonSerializer>();
        return builder;
    }

    /// <summary>Selects one exact contribution for one exact shell profile.</summary>
    public static IServiceCollection AddJsonSerializationContribution(
        this IServiceCollection services,
        JsonSerializationProfileRef profileReference,
        JsonSerializationContribution contribution)
    {
        ArgumentNullException.ThrowIfNull(services);
        services
            .AddProgramKitJson()
            .AddJsonSerializationContribution(profileReference, contribution);
        return services;
    }

    private static bool TryGetCompleteRegistration(
        IServiceCollection services,
        out IProgramKitJsonBuilder builder)
    {
        var ownedDescriptors = services
            .Where(static descriptor =>
                IsProgramKitJsonService(descriptor.ServiceType))
            .ToArray();
        if (ownedDescriptors.Length == 0)
        {
            builder = null!;
            return false;
        }

        var builderDescriptor = SingleDescriptor(
            ownedDescriptors,
            typeof(IProgramKitJsonBuilder));
        var markerDescriptor = SingleDescriptor(
            ownedDescriptors,
            typeof(ProgramKitJsonRegistrationMarker));
        var registryFactoryDescriptor = SingleDescriptor(
            ownedDescriptors,
            typeof(IProgramKitJsonRegistryFactory));
        var registryDescriptor = SingleDescriptor(
            ownedDescriptors,
            typeof(IProgramKitJsonRegistry));
        var canonicalizerDescriptor = SingleDescriptor(
            ownedDescriptors,
            typeof(IProgramKitJsonCanonicalizer));
        var serializerDescriptor = SingleDescriptor(
            ownedDescriptors,
            typeof(IProgramKitJsonSerializer));
        if (ownedDescriptors.Length == 6 &&
            builderDescriptor is
            {
                Lifetime: ServiceLifetime.Singleton,
                ImplementationInstance: ProgramKitJsonBuilder existingBuilder,
            } &&
            markerDescriptor is
            {
                Lifetime: ServiceLifetime.Singleton,
                ImplementationInstance:
                    ProgramKitJsonRegistrationMarker registrationMarker,
            } &&
            ReferenceEquals(registrationMarker.Services, services) &&
            ReferenceEquals(registrationMarker.Builder, existingBuilder) &&
            registryFactoryDescriptor is
            {
                Lifetime: ServiceLifetime.Singleton,
            } &&
            ReferenceEquals(
                registryFactoryDescriptor.ImplementationInstance,
                existingBuilder.RegistryFactory) &&
            registryDescriptor is
            {
                Lifetime: ServiceLifetime.Singleton,
                ImplementationFactory: not null,
            } &&
            ReferenceEquals(
                registryDescriptor.ImplementationFactory,
                registrationMarker.RegistryResolver) &&
            canonicalizerDescriptor is
            {
                Lifetime: ServiceLifetime.Singleton,
                ImplementationType: not null,
            } &&
            canonicalizerDescriptor.ImplementationType ==
                typeof(ProgramKitJsonCanonicalizer) &&
            serializerDescriptor is
            {
                Lifetime: ServiceLifetime.Singleton,
                ImplementationType: not null,
            } &&
            serializerDescriptor.ImplementationType ==
                typeof(ProgramKitJsonSerializer))
        {
            builder = existingBuilder;
            return true;
        }

        throw new InvalidOperationException(
            "The service collection contains a partial, duplicate, or foreign " +
            "Program Kit JSON registration. AddProgramKitJson must own the " +
            "complete shell-scoped registration set.");
    }

    private static ServiceDescriptor? SingleDescriptor(
        IEnumerable<ServiceDescriptor> descriptors,
        Type serviceType)
    {
        ServiceDescriptor? result = null;
        foreach (var descriptor in descriptors)
        {
            if (descriptor.ServiceType != serviceType)
            {
                continue;
            }

            if (result is not null)
            {
                return null;
            }

            result = descriptor;
        }

        return result;
    }

    private static bool IsProgramKitJsonService(Type serviceType) =>
        serviceType == typeof(ProgramKitJsonRegistrationMarker) ||
        serviceType == typeof(IProgramKitJsonRegistryFactory) ||
        serviceType == typeof(IProgramKitJsonBuilder) ||
        serviceType == typeof(IProgramKitJsonRegistry) ||
        serviceType == typeof(IProgramKitJsonCanonicalizer) ||
        serviceType == typeof(IProgramKitJsonSerializer);

    private static IProgramKitJsonRegistry ResolveOwnedRegistry(
        IServiceProvider provider) =>
        provider.GetRequiredService<IProgramKitJsonBuilder>().Freeze();
}
