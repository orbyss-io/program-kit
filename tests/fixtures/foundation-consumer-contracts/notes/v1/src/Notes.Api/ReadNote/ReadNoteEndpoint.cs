using Microsoft.AspNetCore.Http;
using Notes.Core;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails;
using Orbyss.Foundation.Web.ProblemDetails.Core;

namespace Notes.Api.ReadNote;

internal sealed class ReadNoteEndpoint(INoteQueries queries, NoteOwnerAdapter owners,
    IJsonResponseFactory<ReadNoteResponse> responses, IProblemMapper<NoteFailure> problems)
{
    internal async Task<IResult> HandleAsync(HttpContext http, Guid noteId)
    {
        var result = await queries.ReadAsync(owners.Read(http), noteId, http.RequestAborted);
        return result.Value is { } value ? responses.Create(new(NoteWire.From(value)))
            : FoundationProblemResults.Problem(problems.Map(result.Failure!.Value));
    }
}
