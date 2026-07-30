using System.Text.Json.Serialization;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Observability;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Operations.TransportFailures;
using Orbyss.ProgramKit.DotNet.Operations.Security;
using Orbyss.ProgramKit.DotNet.Operations.FastEndpoints;
using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Composition;

[JsonSourceGenerationOptions(
    DefaultIgnoreCondition = JsonIgnoreCondition.Never,
    GenerationMode = JsonSourceGenerationMode.Metadata,
    NumberHandling = JsonNumberHandling.Strict,
    PropertyNameCaseInsensitive = false,
    RespectNullableAnnotations = true,
    RespectRequiredConstructorParameters = true,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(DotNetShellDocument))]
[JsonSerializable(typeof(DotNetConfigurationProviderCatalogDocument))]
[JsonSerializable(typeof(DotNetTelemetryConfiguration))]
[JsonSerializable(typeof(DotNetTransportFailureConfiguration))]
[JsonSerializable(typeof(DotNetSecurityConfiguration))]
[JsonSerializable(typeof(DotNetFastEndpointsConfiguration))]
[JsonSerializable(typeof(DotNetArtifactInputManifest))]
[JsonSerializable(typeof(DotNetArtifactInputManifestAlpha1))]
[JsonSerializable(typeof(DotNetShellLockDocument))]
[JsonSerializable(typeof(DotNetConsoleBindingDocument))]
[JsonSerializable(typeof(DotNetConsoleInputMaterializationRequest))]
[JsonSerializable(typeof(DotNetConsoleInputMaterializationRequestAlpha2))]
[JsonSerializable(typeof(DotNetConsoleCommandSketch))]
[JsonSerializable(typeof(DotNetConsoleContractStyleCatalog))]
[JsonSerializable(typeof(DotNetConsoleContractStyleCommands))]
[JsonSerializable(typeof(DotNetConsoleContractStyleRule))]
[JsonSerializable(typeof(DotNetConsoleLogicalClrType))]
[JsonSerializable(typeof(DotNetConsoleInputMaterializationLock))]
[JsonSerializable(typeof(OpenApiDocumentProjection))]
[JsonSerializable(typeof(OpenConsoleDocument))]
[JsonSerializable(typeof(OpenConsoleDocumentAlpha2))]
[JsonSerializable(typeof(OpenWorkerDocument))]
[JsonSerializable(typeof(SecretResolutionContract))]
[JsonSerializable(typeof(SecretChangeSignal))]
[JsonSerializable(typeof(SecretReactionResult))]
internal sealed partial class DotNetShellJsonContext : JsonSerializerContext;
