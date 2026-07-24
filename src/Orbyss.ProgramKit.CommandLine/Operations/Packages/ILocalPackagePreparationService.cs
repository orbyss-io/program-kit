namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Prepares a finite explicit package selection into one hash-bound local root.</summary>
public interface ILocalPackagePreparationService
{
    /// <summary>Packs and validates exactly the manifest-selected projects.</summary>
    ValueTask<LocalPackagePreparationResult> PrepareAsync(
        LocalPackagePreparationRequest request,
        CancellationToken cancellationToken);
}
