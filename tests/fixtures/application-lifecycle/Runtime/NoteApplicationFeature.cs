using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
namespace ProgramKit.Examples.Events;
[ShellFeature("Note.Application")]
public sealed class NoteApplicationFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services) => services.AddScoped<NoteApplication>();
}
