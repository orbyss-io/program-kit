namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Materializes one exact reviewed Kiota tool archive into staging.</summary>
public interface IKiotaToolPackageMaterializer
{
    /// <summary>Returns the verified staged Kiota entry assembly path.</summary>
    ValueTask<string> MaterializeAsync(
        string packagePath,
        string outputRoot,
        CancellationToken cancellationToken);
}
