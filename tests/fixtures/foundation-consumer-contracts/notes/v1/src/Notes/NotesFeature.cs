using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using Notes.Core;

namespace Notes;

[ShellFeature("Notes")]
public sealed class NotesFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services) => services.AddSingleton<INoteAuthoring, NoteAuthoring>();
}
