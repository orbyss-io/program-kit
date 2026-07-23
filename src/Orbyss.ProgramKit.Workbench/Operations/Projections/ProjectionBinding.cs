namespace Orbyss.ProgramKit.Workbench.Operations.Projections;

/// <summary>Binds one declared projection input to the currently observed exact input.</summary>
/// <param name="Declared">Exact input used by the generated projection.</param>
/// <param name="Current">Exact input currently selected for comparison.</param>
public sealed record ProjectionBinding(
    ArtifactReference Declared,
    ArtifactReference Current);
