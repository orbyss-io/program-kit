using Microsoft.AspNetCore.Http;
using Notes.Core;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails;
using Orbyss.Foundation.Web.ProblemDetails.Core;

namespace Notes.Api.RenameNote;

internal sealed class RenameNoteEndpoint(INoteAuthoring authoring, NoteOwnerAdapter owners,
    IJsonRequestReader<RenameNoteRequest> requests, IJsonResponseFactory<RenameNoteResponse> responses,
    IProblemMapper<NoteFailure> problems)
{
    internal async Task<IResult> HandleAsync(HttpContext http, Guid noteId)
    {
        var packet = await requests.ReadAsync(http, http.RequestAborted);
        var result = await authoring.RenameAsync(owners.Read(http), packet.OperationId, noteId,
            packet.ExpectedRevision, packet.Name, http.RequestAborted);
        return result.Value is { } value ? responses.Create(new(value.OperationId, NoteWire.From(value.Note)))
            : FoundationProblemResults.Problem(problems.Map(result.Failure!.Value));
    }
}
