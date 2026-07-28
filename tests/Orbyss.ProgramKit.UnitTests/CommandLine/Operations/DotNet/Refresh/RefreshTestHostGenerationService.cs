using System.Text;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Publication;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Sealing;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Refresh;

internal sealed class RefreshTestHostGenerationService :
    IDotNetHostGenerationCommandService
{
    internal string Content { get; set; } = "first\n";

    public async ValueTask<DotNetHostGenerationCommandResult> GenerateAsync(
        DotNetHostGenerationCommandRequest request,
        CancellationToken cancellationToken)
    {
        GeneratedOutputPublisher publisher = new(
            new GeneratedOutputSealer(),
            new GeneratedOutputIntegrityVerifier());
        _ = await publisher.PublishCreateAsync(
            request.OutputRoot,
            [
                new GeneratedOutputPayload(
                    "ProgramKitGenerated/Program.cs",
                    Encoding.UTF8.GetBytes(Content)),
            ],
            cancellationToken);
        return null!;
    }
}
