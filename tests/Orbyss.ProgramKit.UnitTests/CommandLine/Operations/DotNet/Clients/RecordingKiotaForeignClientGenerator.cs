using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Clients;

internal sealed class RecordingKiotaForeignClientGenerator :
    IKiotaForeignClientGenerator
{
    internal KiotaForeignClientGenerationRequest? Request { get; private set; }

    public ValueTask<KiotaForeignClientGenerationResult> GenerateAsync(
        KiotaForeignClientGenerationRequest request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        Request = request;
        Sha256Digest digest = new(
            "sha256:0000000000000000000000000000000000000000000000000000000000000000");
        return ValueTask.FromResult(
            new KiotaForeignClientGenerationResult(
                request.OutputRoot,
                digest,
                digest,
                digest,
                [],
                []));
    }
}
