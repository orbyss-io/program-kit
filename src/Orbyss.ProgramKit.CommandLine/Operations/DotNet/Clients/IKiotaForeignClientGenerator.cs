namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Generates one exact foreign C# client through the pinned Kiota tool.</summary>
public interface IKiotaForeignClientGenerator
{
    /// <summary>Generates into one explicit absent output root.</summary>
    ValueTask<KiotaForeignClientGenerationResult> GenerateAsync(
        KiotaForeignClientGenerationRequest request,
        CancellationToken cancellationToken);
}
