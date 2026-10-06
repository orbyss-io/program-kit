using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Options;
using Notes.Core;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails;
using Orbyss.Foundation.Web.ProblemDetails.Core;

namespace Notes.Api.ListNotes;

internal sealed class ListNotesEndpoint(INoteQueries queries, NoteOwnerAdapter owners,
    IJsonResponseFactory<ListNotesResponse> responses, IProblemMapper<NoteFailure> problems, IOptions<FoundationJsonOptions> json)
{
    internal async Task<IResult> HandleAsync(HttpContext http, Guid? after, int? size)
    {
        var result = await queries.ListAsync(owners.Read(http), after, json.Value.Paging.Admit(size), http.RequestAborted);
        return result.Value is { } value ? responses.Create(new(value.Items.Select(NoteWire.From).ToArray(), value.NextAfterNoteId))
            : FoundationProblemResults.Problem(problems.Map(result.Failure!.Value));
    }
}
