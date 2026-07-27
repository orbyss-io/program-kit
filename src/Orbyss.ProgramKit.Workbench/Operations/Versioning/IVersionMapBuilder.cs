namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Builds an immutable exact Version Map from reviewed manifests.</summary>
public interface IVersionMapBuilder
{
    /// <summary>Validates and deterministically constructs one map revision payload.</summary>
    WorkbenchResult<VersionMapDocument> Build(VersionMapBuildRequest request);
}
