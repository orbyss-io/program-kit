using CShells.Features;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.DomainEvents;

/// <summary>Composes in-process domain-event publication into one CShells generation.</summary>
[ShellFeature(
    name: "ProgramKit.DomainEvents",
    DisplayName = "Program Kit Domain Events",
    Description = "Provides awaited, scoped, non-durable publication of domain-owned events.")]
public sealed class ProgramKitDomainEventsFeature : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services) => services.AddProgramKitDomainEvents();
}
