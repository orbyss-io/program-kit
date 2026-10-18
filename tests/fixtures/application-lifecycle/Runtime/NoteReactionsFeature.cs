using CShells;
using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.DomainEvents;
namespace ProgramKit.Examples.Events;
/// <summary>Independent observer owner references Core and abstractions, never the dispatcher implementation.</summary>
[ShellFeature("Note.Reactions")]
public sealed class NoteReactionsFeature(ShellSettings settings) : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<ReactionObservation>();
        var configuration = settings.GetConfigurationRoot();
        var missing = configuration["Fixture:MissingHandler"] == "true";
        if (!missing)
        {
            services.AddScoped<IDomainEventHandler<NoteSaved>, NoteSavedReaction>();
            services.AddScoped<IDomainEventHandler<NoteSaved>, SecondReaction>();
        }
        services.AddScoped<IDomainEventHandler<ReactionFault>, FaultingReaction>();
        services.AddScoped<IDomainEventHandler<WaitingFact>, WaitingReaction>();
    }
}
