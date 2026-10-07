using CShells;
using CShells.Features;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Notes.Core;
using Orbyss.Foundation.PostgreSql;

namespace Notes.PostgreSql;

[ShellFeature("Notes.PostgreSql")]
public sealed class NotesPostgreSqlFeature(ShellSettings settings) : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        var options = settings.GetConfigurationRoot().GetSection("Foundation:PostgreSql:Policies:" + StorageNames.Policy)
            .Get<PostgreSqlOptions>() ?? throw new InvalidOperationException("The Notes database policy is required.");
        services.AddFoundationPostgreSql<NotesDbContext>(StorageNames.Policy, options, admitted => new NotesDbContext(admitted));
        services.AddSingleton(new NoteOperationBudget(options.OperationTimeout));
        services.AddSingleton<INoteRevisionLifecycle, NoteRevisionLifecycle>();
        services.AddSingleton<INoteQueries, NoteQueries>();
    }
}
