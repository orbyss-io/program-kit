using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Notes.Api.CreateNote;
using Notes.Api.ListNotes;
using Notes.Api.ReadNote;
using Notes.Api.RenameNote;
using Notes.Core;
using Orbyss.Foundation.Authentication;
using Orbyss.Foundation.Authentication.BffCookie;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails.Core;

namespace Notes.Api;

[ShellFeature("Notes.Api", DependsOn = [typeof(FoundationAuthenticationFeature), typeof(FoundationJsonFeature), typeof(FoundationBffCookieFeature)])]
public sealed class NotesApiFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        FixtureAuthenticationAliases.Register(services);
        services.AddSingleton<NoteOwnerAdapter>();
        services.AddSingleton<IProblemMapper<NoteFailure>, NoteProblemMapper>();
        services.AddTransient<CreateNoteEndpoint>();
        services.AddTransient<ReadNoteEndpoint>();
        services.AddTransient<RenameNoteEndpoint>();
        services.AddTransient<ListNotesEndpoint>();
        services.AddJsonRequestContract<CreateNoteRequest>(new(JsonProfileKeys.StrictRequest), new(JsonProfileKeys.StrictRequest));
        services.AddJsonRequestContract<RenameNoteRequest>(new(JsonProfileKeys.StrictRequest), new(JsonProfileKeys.StrictRequest));
        services.AddJsonResponseContract<CreateNoteResponse>(new(JsonProfileKeys.SuccessResponse), new(JsonProfileKeys.TolerantResponse));
        services.AddJsonResponseContract<ReadNoteResponse>(new(JsonProfileKeys.SuccessResponse), new(JsonProfileKeys.TolerantResponse));
        services.AddJsonResponseContract<RenameNoteResponse>(new(JsonProfileKeys.SuccessResponse), new(JsonProfileKeys.TolerantResponse));
        services.AddJsonResponseContract<ListNotesResponse>(new(JsonProfileKeys.SuccessResponse), new(JsonProfileKeys.TolerantResponse));
    }

    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        endpoints.MapPost("/api/notes", (HttpContext http, [FromServices] CreateNoteEndpoint operation) => operation.HandleAsync(http))
            .WithJsonRequest<CreateNoteRequest>().WithJsonResponse<CreateNoteResponse>().RequireAuthorization();
        endpoints.MapGet("/api/notes/{noteId:guid}", (HttpContext http, Guid noteId, [FromServices] ReadNoteEndpoint operation) => operation.HandleAsync(http, noteId))
            .WithJsonResponse<ReadNoteResponse>().RequireAuthorization();
        endpoints.MapPost("/api/notes/{noteId:guid}/rename", (HttpContext http, Guid noteId, [FromServices] RenameNoteEndpoint operation) => operation.HandleAsync(http, noteId))
            .WithJsonRequest<RenameNoteRequest>().WithJsonResponse<RenameNoteResponse>().RequireAuthorization();
        endpoints.MapGet("/api/notes", (HttpContext http, Guid? after, int? size, [FromServices] ListNotesEndpoint operation) => operation.HandleAsync(http, after, size))
            .WithJsonResponse<ListNotesResponse>().RequireAuthorization();
    }
}
