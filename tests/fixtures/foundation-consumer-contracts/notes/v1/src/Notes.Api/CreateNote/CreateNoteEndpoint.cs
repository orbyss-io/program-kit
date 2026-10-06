using Microsoft.AspNetCore.Http;
using Notes.Core;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails;
using Orbyss.Foundation.Web.ProblemDetails.Core;

namespace Notes.Api.CreateNote;

internal sealed class CreateNoteEndpoint(INoteAuthoring authoring, NoteOwnerAdapter owners,
    IJsonRequestReader<CreateNoteRequest> requests, IJsonResponseFactory<CreateNoteResponse> responses,
    IProblemMapper<NoteFailure> problems)
{
    internal async Task<IResult> HandleAsync(HttpContext http)
    {
        var packet = await requests.ReadAsync(http, http.RequestAborted);
        var result = await authoring.CreateAsync(owners.Read(http), packet.OperationId, packet.NoteId, packet.Name, http.RequestAborted);
        return result.Value is { } value ? responses.Create(new(value.OperationId, NoteWire.From(value.Note)))
            : FoundationProblemResults.Problem(problems.Map(result.Failure!.Value));
    }
}
