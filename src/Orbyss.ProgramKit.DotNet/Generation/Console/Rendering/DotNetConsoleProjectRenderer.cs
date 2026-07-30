using System.Text;
using Orbyss.ProgramKit.DotNet.Generation.Console.Projection;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Rendering;

internal sealed class DotNetConsoleProjectRenderer :
    IDotNetConsoleOutputRenderer
{
    public ImmutableArray<GeneratedOutput> Render(
        DotNetConsoleHostProjection projection) =>
        [
            Output("global.json", GlobalJson()),
            Output("Directory.Build.props", BuildProps()),
            Output(
                "Directory.Build.targets",
                DotNetGeneratedProjectBuildTargets.Content),
            Output("Directory.Packages.props", "<Project />\n"),
            Output("GeneratedHost.csproj", Project(projection)),
            Output(
                "ProgramKitGenerated/Hosting/ProgramKitGeneratedIntegrityRequirement.cs",
                IntegrityRequirement()),
        ];

    private static GeneratedOutput Output(string path, string content) =>
        new(path, DotNetSourceText.Utf8(content));

    private static string GlobalJson() =>
        """
        {
          "sdk": {
            "version": "10.0.302",
            "rollForward": "disable",
            "allowPrerelease": false
          }
        }

        """;

    private static string BuildProps() =>
        """
        <Project>
          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <LangVersion>14.0</LangVersion>
            <Nullable>enable</Nullable>
            <ImplicitUsings>disable</ImplicitUsings>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <CodeAnalysisTreatWarningsAsErrors>true</CodeAnalysisTreatWarningsAsErrors>
            <MSBuildTreatWarningsAsErrors>true</MSBuildTreatWarningsAsErrors>
            <RestoreTreatWarningsAsErrors>true</RestoreTreatWarningsAsErrors>
            <NoWarn>__ProgramKitNoWarningSuppression__</NoWarn>
            <WarningsNotAsErrors>__ProgramKitNoWarningDemotion__</WarningsNotAsErrors>
            <TargetFrameworks></TargetFrameworks>
            <WarningsAsErrors />
            <Deterministic>true</Deterministic>
            <ContinuousIntegrationBuild>true</ContinuousIntegrationBuild>
            <BaseOutputPath>$(MSBuildProjectDirectory)\..\.program-kit-build\$([System.IO.Path]::GetFileName('$(MSBuildProjectDirectory)'))\bin\</BaseOutputPath>
            <BaseIntermediateOutputPath>$(MSBuildProjectDirectory)\..\.program-kit-build\$([System.IO.Path]::GetFileName('$(MSBuildProjectDirectory)'))\obj\</BaseIntermediateOutputPath>
            <OutputPath>$(BaseOutputPath)$(Configuration)\$(TargetFramework)\</OutputPath>
            <IntermediateOutputPath>$(BaseIntermediateOutputPath)$(Configuration)\$(TargetFramework)\</IntermediateOutputPath>
            <MSBuildProjectExtensionsPath>$(BaseIntermediateOutputPath)</MSBuildProjectExtensionsPath>
          </PropertyGroup>
        </Project>

        """;

    private static string Project(DotNetConsoleHostProjection projection)
    {
        StringBuilder builder = new();
        DotNetConsoleRendering.Line(
            builder,
            0,
            "<Project Sdk=\"Microsoft.NET.Sdk\">");
        DotNetConsoleRendering.Line(builder, 1, "<PropertyGroup>");
        DotNetConsoleRendering.Line(
            builder,
            2,
            "<OutputType>Exe</OutputType>");
        DotNetConsoleRendering.Line(
            builder,
            2,
            string.Concat(
                "<AssemblyName>",
                DotNetSourceText.Xml(projection.AssemblyName),
                "</AssemblyName>"));
        DotNetConsoleRendering.Line(builder, 1, "</PropertyGroup>");
        DotNetConsoleRendering.Line(builder, 1, "<ItemGroup>");
        DotNetConsoleRendering.Line(
            builder,
            2,
            "<PackageReference Include=\"CShells\" Version=\"[0.0.28]\" />");
        DotNetConsoleRendering.Line(
            builder,
            2,
            "<PackageReference Include=\"Microsoft.Extensions.DependencyInjection\" Version=\"[10.0.10]\" />");
        DotNetConsoleRendering.Line(
            builder,
            2,
            "<PackageReference Include=\"Spectre.Console\" Version=\"[0.55.0]\" />");
        DotNetConsoleRendering.Line(
            builder,
            2,
            "<PackageReference Include=\"Spectre.Console.Cli\" Version=\"[0.55.0]\" />");
        DotNetConsoleRendering.Line(
            builder,
            2,
            "<PackageReference Include=\"Orbyss.ProgramKit.GeneratedOutputIntegrity.Build\" Version=\"[0.1.0-alpha.3]\" PrivateAssets=\"all\" />");
        DotNetConsoleRendering.Line(builder, 1, "</ItemGroup>");
        DotNetConsoleRendering.Line(builder, 1, "<ItemGroup>");
        DotNetConsoleRendering.Line(
            builder,
            2,
            string.Concat(
                "<ProjectReference Include=\"",
                DotNetSourceText.Xml(projection.ConsumerProjectPath),
                "\" />"));
        DotNetConsoleRendering.Line(builder, 1, "</ItemGroup>");
        DotNetConsoleRendering.Line(builder, 0, "</Project>");
        return builder.ToString();
    }

    private static string IntegrityRequirement() =>
        """
        // <auto-generated program-kit>
        namespace GeneratedHost.Hosting;

        internal sealed class ProgramKitGeneratedIntegrityRequirement :
            ProgramKitGeneratedIntegrityAttestation;

        """;
}
