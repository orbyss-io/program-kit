namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>
/// Shared generated-project verification entry point for every generated host.
/// </summary>
internal static class DotNetGeneratedProjectBuildTargets
{
    /// <summary>Gets the exact deterministic Directory.Build.targets bytes.</summary>
    public const string Content =
        """
        <Project>
          <Target Name="ProgramKitConfigureGeneratedProjectVerification">
            <PropertyGroup>
              <ProgramKitCSharpGateGeneratedProjectBinding>1.0.0</ProgramKitCSharpGateGeneratedProjectBinding>
            </PropertyGroup>
          </Target>

          <Target Name="ProgramKitVerifyGeneratedProject"
                  DependsOnTargets="ProgramKitConfigureGeneratedProjectVerification;Build" />
        </Project>

        """;
}
