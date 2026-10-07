using Notes.Core;
using Orbyss.Foundation.Web.ProblemDetails.Core;

namespace Notes.Api;

internal sealed class NoteProblemMapper : IProblemMapper<NoteFailure>
{
    public ProblemDefinition Map(NoteFailure failure) => failure switch
    {
        NoteFailure.InvalidName => new(400, "note_name_invalid"),
        NoteFailure.InvalidIdentity => new(400, "note_identity_invalid"),
        NoteFailure.NotFound => new(404, "note_not_found"),
        NoteFailure.NoteConflict => new(409, "note_conflict"),
        NoteFailure.RevisionConflict => new(409, "note_revision_conflict"),
        NoteFailure.OperationConflict => new(409, "note_operation_conflict"),
        NoteFailure.Unavailable => new(503, "note_unavailable"),
        NoteFailure.Uncertain => new(503, "note_commit_uncertain"),
        _ => throw new InvalidOperationException("Unknown note outcome.")
    };
}
