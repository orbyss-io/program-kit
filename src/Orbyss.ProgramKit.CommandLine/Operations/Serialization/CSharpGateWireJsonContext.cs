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
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    RespectNullableAnnotations = true,
    RespectRequiredConstructorParameters = true,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(CSharpBuildGateDefinitionDocument))]
[JsonSerializable(typeof(CSharpGateRuleCatalog))]
[JsonSerializable(typeof(CSharpGateActivationMatrix))]
[JsonSerializable(typeof(CSharpGateSuppressionLedger))]
[JsonSerializable(typeof(ConsumerAnalyzerScaffoldRequest))]
[JsonSerializable(typeof(CSharpGateBindRequest))]
[JsonSerializable(typeof(CSharpGateBindRequestAlpha1))]
[JsonSerializable(typeof(CSharpGateLockIntent))]
[JsonSerializable(typeof(CSharpGateLockInputProjection))]
[JsonSerializable(typeof(CSharpGateSelectionLockOutputProjection))]
[JsonSerializable(typeof(CSharpBuildGateSelectionLockDocument))]
[JsonSerializable(typeof(CSharpBuildGateSelectionLockDocumentAlpha1))]
[JsonSerializable(typeof(CSharpGateVerificationRequest))]
[JsonSerializable(typeof(CSharpGateCompilerHarnessResult))]
internal sealed partial class CSharpGateWireJsonContext : JsonSerializerContext;
