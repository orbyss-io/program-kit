namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>Generates one deterministic AppHost without restoring, running, or deploying it.</summary>
public interface IAspireAppHostGenerator
{
    /// <summary>Validates and renders one complete AppHost projection.</summary>
    AspireAppHostGenerationResult Generate(AspireAppHostDefinition definition);
}
