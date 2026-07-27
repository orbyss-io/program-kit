using Microsoft.AspNetCore.Http.Features;

namespace GeneratedHost.Composition;

internal sealed class StartedResponseFeature : HttpResponseFeature
{
    public override bool HasStarted => true;
}
