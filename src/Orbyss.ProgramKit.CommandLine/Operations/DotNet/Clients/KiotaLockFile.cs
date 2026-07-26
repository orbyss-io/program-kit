using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

internal sealed record KiotaLockFile(
    string DescriptionHash,
    string DescriptionLocation,
    string LockFileVersion,
    string KiotaVersion,
    string ClientClassName,
    string TypeAccessModifier,
    string ClientNamespaceName,
    string Language,
    bool UsesBackingStore,
    bool ExcludeBackwardCompatible,
    bool IncludeAdditionalData,
    bool DisableSslValidation,
    ImmutableArray<string> Serializers,
    ImmutableArray<string> Deserializers,
    ImmutableArray<string> StructuredMimeTypes,
    ImmutableArray<string> IncludePatterns,
    ImmutableArray<string> ExcludePatterns,
    ImmutableArray<string> DisabledValidationRules,
    ImmutableArray<string> AllowedExternalOrigins);
