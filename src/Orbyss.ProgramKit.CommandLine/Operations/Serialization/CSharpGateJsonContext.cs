using System.Text.Json.Serialization;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;
namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

[JsonSourceGenerationOptions(
    DefaultIgnoreCondition = JsonIgnoreCondition.Never,
    GenerationMode = JsonSourceGenerationMode.Metadata,
    NumberHandling = JsonNumberHandling.Strict,
    PropertyNameCaseInsensitive = false,
    RespectNullableAnnotations = true,
    RespectRequiredConstructorParameters = true,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(CSharpGateJsonProfileMarker))]
[JsonSerializable(typeof(CSharpBuildGateDefinitionDocument))]
[JsonSerializable(typeof(ConsumerAnalyzerScaffoldRequest))]
[JsonSerializable(typeof(CSharpGateBindRequest))]
[JsonSerializable(typeof(CSharpBuildGateSelectionLockDocument))]
[JsonSerializable(typeof(CSharpGateVerificationRequest))]
[JsonSerializable(typeof(CSharpGateCompilerHarnessResult))]
internal sealed partial class CSharpGateJsonContext : JsonSerializerContext;
