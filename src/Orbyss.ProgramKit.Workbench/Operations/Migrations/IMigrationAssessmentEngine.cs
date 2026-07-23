namespace Orbyss.ProgramKit.Workbench.Operations.Migrations;

/// <summary>Computes complete deterministic reverse migration closure.</summary>
public interface IMigrationAssessmentEngine
{
    /// <summary>Assesses every changed root and reached dependent.</summary>
    WorkbenchResult<MigrationAssessment> Assess(MigrationAssessmentRequest request);
}
