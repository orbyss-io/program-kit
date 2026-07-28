using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Offline metadata verifier for exact consumer Console contracts.</summary>
public sealed class DotNetConsoleMetadataInspector :
    IDotNetConsoleMetadataInspector
{
    private static readonly HashSet<string> ForbiddenDependencies =
        new(
            [
                "System.IServiceProvider",
                "Microsoft.Extensions.DependencyInjection.IServiceScopeFactory",
                "Microsoft.Extensions.DependencyInjection.IServiceCollection",
            ],
            StringComparer.Ordinal);

    /// <inheritdoc />
    public DotNetConsoleMetadataInspectionResult Inspect(
        DotNetConsoleBindingDocument binding,
        string referenceAssemblyPath)
    {
        ArgumentNullException.ThrowIfNull(binding);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (string.IsNullOrWhiteSpace(referenceAssemblyPath) ||
            !File.Exists(referenceAssemblyPath))
        {
            Error(
                diagnostics,
                "The exact consumer reference assembly is missing.",
                "/consumerProject/relativeReferenceAssemblyPath");
            return Invalid(diagnostics);
        }

        try
        {
            using FileStream stream = new(
                referenceAssemblyPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read);
            var actualDigest = new Sha256Digest(
                string.Concat(
                    "sha256:",
                    Convert.ToHexStringLower(SHA256.HashData(stream))));
            if (actualDigest != binding.ConsumerProject.ReferenceAssemblyDigest)
            {
                Error(
                    diagnostics,
                    "The consumer reference assembly digest is stale or mismatched.",
                    "/consumerProject/referenceAssemblyDigest");
                return Invalid(diagnostics);
            }

            stream.Position = 0;
            using PEReader peReader = new(stream, PEStreamOptions.LeaveOpen);
            if (!peReader.HasMetadata)
            {
                Error(
                    diagnostics,
                    "The consumer reference assembly does not contain managed metadata.",
                    "/consumerProject");
                return Invalid(diagnostics);
            }

            var metadata = peReader.GetMetadataReader();
            var assemblyName = metadata.GetString(
                metadata.GetAssemblyDefinition().Name);
            if (assemblyName != binding.ConsumerProject.ReferenceAssemblyName)
            {
                Error(
                    diagnostics,
                    "The reference assembly identity does not match the binding.",
                    "/consumerProject/referenceAssemblyName");
            }

            Dictionary<string, TypeDefinitionHandle> types =
                metadata.TypeDefinitions.ToDictionary(
                    handle => MetadataTypeNames.Definition(metadata, handle),
                    StringComparer.Ordinal);
            var verified = ImmutableArray.CreateBuilder<string>();
            VerifyFeature(binding.FeatureType, metadata, types, verified, diagnostics);
            VerifyValidationResult(
                binding.ValidationResultType,
                metadata,
                types,
                verified,
                diagnostics);
            foreach (var operation in binding.Operations)
            {
                VerifyOperation(
                    operation,
                    binding.ValidationResultType,
                    metadata,
                    types,
                    verified,
                    diagnostics);
            }

            VerifyImplementationConstructors(
                binding,
                metadata,
                diagnostics);
            return diagnostics.Any(static diagnostic =>
                    diagnostic.Severity == ProgramKitDiagnosticSeverity.Error)
                ? Invalid(diagnostics)
                : new DotNetConsoleMetadataInspectionResult(
                    true,
                    new DotNetConsoleMetadataProof(
                        actualDigest,
                        verified
                            .Distinct(StringComparer.Ordinal)
                            .Order(StringComparer.Ordinal)
                            .ToImmutableArray()),
                    diagnostics.ToImmutable());
        }
        catch (Exception exception) when (
            exception is BadImageFormatException or
                IOException or
                UnauthorizedAccessException)
        {
            Error(
                diagnostics,
                "The consumer reference assembly metadata is malformed or unreadable.",
                "/consumerProject");
            return Invalid(diagnostics);
        }
    }

    private static void VerifyFeature(
        DotNetConsoleClrTypeDescriptor descriptor,
        MetadataReader metadata,
        IReadOnlyDictionary<string, TypeDefinitionHandle> types,
        ImmutableArray<string>.Builder verified,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!TryType(descriptor, types, "/featureType", diagnostics, out var handle))
        {
            return;
        }

        var definition = metadata.GetTypeDefinition(handle);
        var valid = IsPublic(definition.Attributes) &&
                    definition.Attributes.HasFlag(TypeAttributes.Sealed) &&
                    !definition.Attributes.HasFlag(TypeAttributes.Abstract) &&
                    !definition.Attributes.HasFlag(TypeAttributes.Interface) &&
                    definition.GetGenericParameters().Count == 0 &&
                    descriptor.ReferenceNullability ==
                        DotNetConsoleReferenceNullability.NotNull &&
                    Implements(
                        metadata,
                        definition,
                        "CShells.Features.IShellFeature") &&
                    HasPublicParameterlessConstructor(metadata, definition);
        if (!valid)
        {
            Error(
                diagnostics,
                "The Console feature must be public, sealed, concrete, nongeneric, non-null, parameterless, and implement CShells.Features.IShellFeature.",
                "/featureType");
            return;
        }

        verified.Add(descriptor.MetadataName);
    }

    private static void VerifyValidationResult(
        DotNetConsoleClrTypeDescriptor descriptor,
        MetadataReader metadata,
        IReadOnlyDictionary<string, TypeDefinitionHandle> types,
        ImmutableArray<string>.Builder verified,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!TryType(
                descriptor,
                types,
                "/validationResultType",
                diagnostics,
                out var handle))
        {
            return;
        }

        var definition = metadata.GetTypeDefinition(handle);
        var valid = IsPublic(definition.Attributes) &&
                    definition.Attributes.HasFlag(TypeAttributes.Sealed) &&
                    !definition.Attributes.HasFlag(TypeAttributes.Abstract) &&
                    !definition.Attributes.HasFlag(TypeAttributes.Interface) &&
                    definition.GetGenericParameters().Count == 0 &&
                    descriptor.ReferenceNullability ==
                        DotNetConsoleReferenceNullability.NotNull &&
                    HasPublicReadableProperty(
                        metadata,
                        definition,
                        "IsValid",
                        "System.Boolean") &&
                    HasPublicReadableProperty(
                        metadata,
                        definition,
                        "Messages",
                        "System.Collections.Generic.IReadOnlyList`1<System.String>");
        if (!valid)
        {
            Error(
                diagnostics,
                "The validation result must be one public sealed nongeneric type exposing bool IsValid and IReadOnlyList<string> Messages.",
                "/validationResultType");
            return;
        }

        verified.Add(descriptor.MetadataName);
    }

    private static void VerifyOperation(
        DotNetConsoleOperationBinding operation,
        DotNetConsoleClrTypeDescriptor validationResultType,
        MetadataReader metadata,
        IReadOnlyDictionary<string, TypeDefinitionHandle> types,
        ImmutableArray<string>.Builder verified,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!TryType(
                operation.RequestType,
                types,
                "/operations/requestType",
                diagnostics,
                out var requestHandle) ||
            !TryType(
                operation.HandlerType,
                types,
                "/operations/handlerType",
                diagnostics,
                out var handlerHandle))
        {
            return;
        }

        VerifyRequest(
            operation,
            metadata,
            requestHandle,
            diagnostics);
        VerifyInterfaceMethod(
            metadata,
            handlerHandle,
            operation.HandlerType,
            "HandleAsync",
            string.Concat(
                "System.Threading.Tasks.ValueTask`1<System.Int32>"),
            operation.RequestType,
            "/operations/handlerType",
            diagnostics);
        verified.Add(operation.RequestType.MetadataName);
        verified.Add(operation.HandlerType.MetadataName);

        if (operation.ValidatorType is null)
        {
            return;
        }

        if (!TryType(
                operation.ValidatorType,
                types,
                "/operations/validatorType",
                diagnostics,
                out var validatorHandle))
        {
            return;
        }

        VerifyInterfaceMethod(
            metadata,
            validatorHandle,
            operation.ValidatorType,
            "ValidateAsync",
            string.Concat(
                "System.Threading.Tasks.ValueTask`1<",
                Render(validationResultType),
                ">"),
            operation.RequestType,
            "/operations/validatorType",
            diagnostics);
        verified.Add(operation.ValidatorType.MetadataName);
    }

    private static void VerifyRequest(
        DotNetConsoleOperationBinding operation,
        MetadataReader metadata,
        TypeDefinitionHandle handle,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var definition = metadata.GetTypeDefinition(handle);
        if (!IsPublic(definition.Attributes) ||
            definition.Attributes.HasFlag(TypeAttributes.Abstract) ||
            definition.Attributes.HasFlag(TypeAttributes.Interface) ||
            definition.GetGenericParameters().Count != 0 ||
            operation.RequestType.ReferenceNullability !=
                DotNetConsoleReferenceNullability.NotNull)
        {
            Error(
                diagnostics,
                "Request types must be public, concrete, nongeneric, and non-null.",
                "/operations/requestType");
            return;
        }

        var expectedTypes = operation.ConstructorParameters
            .Select(static parameter => Render(parameter.ClrType))
            .ToArray();
        var expectedNullability = operation.ConstructorParameters
            .Select(static parameter => parameter.ClrType.ReferenceNullability)
            .ToArray();
        var matching = definition.GetMethods()
            .Select(metadata.GetMethodDefinition)
            .Where(method =>
                metadata.GetString(method.Name) == ".ctor" &&
                method.Attributes.HasFlag(MethodAttributes.Public) &&
                !method.Attributes.HasFlag(MethodAttributes.Static))
            .Any(method =>
                MatchesConstructor(
                    metadata,
                    definition,
                    method,
                    expectedTypes,
                    expectedNullability));
        if (!matching)
        {
            Error(
                diagnostics,
                "No public request constructor matches the exact parameter types, order, and nullability.",
                "/operations/constructorParameters");
        }
    }

    private static bool MatchesConstructor(
        MetadataReader metadata,
        TypeDefinition declaringType,
        MethodDefinition method,
        IReadOnlyList<string> expectedTypes,
        DotNetConsoleReferenceNullability[] expectedNullability)
    {
        MetadataTypeNameProvider provider = default;
        var signature = method.DecodeSignature(provider, genericContext: null);
        if (!signature.ParameterTypes.SequenceEqual(expectedTypes))
        {
            return false;
        }

        var parameters = method.GetParameters()
            .Select(metadata.GetParameter)
            .Where(static parameter => parameter.SequenceNumber > 0)
            .OrderBy(static parameter => parameter.SequenceNumber)
            .ToArray();
        for (var index = 0; index < parameters.Length; index++)
        {
            if (expectedNullability[index] ==
                    DotNetConsoleReferenceNullability.NotApplicable)
            {
                continue;
            }

            if (MetadataNullability.Read(
                    metadata,
                    parameters[index],
                    method,
                    declaringType) != expectedNullability[index])
            {
                return false;
            }
        }

        return true;
    }

    private static void VerifyInterfaceMethod(
        MetadataReader metadata,
        TypeDefinitionHandle handle,
        DotNetConsoleClrTypeDescriptor interfaceType,
        string methodName,
        string expectedReturn,
        DotNetConsoleClrTypeDescriptor requestType,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var definition = metadata.GetTypeDefinition(handle);
        MetadataTypeNameProvider provider = default;
        var methods = definition.GetMethods()
            .Select(metadata.GetMethodDefinition)
            .Where(method => metadata.GetString(method.Name) == methodName)
            .ToArray();
        var valid = IsPublic(definition.Attributes) &&
                    definition.Attributes.HasFlag(TypeAttributes.Interface) &&
                    definition.GetGenericParameters().Count == 0 &&
                    interfaceType.ReferenceNullability ==
                        DotNetConsoleReferenceNullability.NotNull &&
                    methods.Length == 1 &&
                    methods[0].Attributes.HasFlag(MethodAttributes.Public) &&
                    methods[0].Attributes.HasFlag(MethodAttributes.Abstract);
        if (valid)
        {
            var signature = methods[0].DecodeSignature(provider, genericContext: null);
            valid = signature.ReturnType == expectedReturn &&
                    signature.ParameterTypes.SequenceEqual(
                        [
                            Render(requestType),
                            "System.Threading.CancellationToken",
                        ]);
        }

        if (!valid)
        {
            Error(
                diagnostics,
                string.Concat(
                    methodName,
                    " must have the exact approved ValueTask signature."),
                path);
        }
    }

    private static void VerifyImplementationConstructors(
        DotNetConsoleBindingDocument binding,
        MetadataReader metadata,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var contracts = binding.Operations
            .SelectMany(static operation =>
                operation.ValidatorType is null
                    ? new[] { operation.HandlerType.MetadataName }
                    : new[]
                    {
                        operation.HandlerType.MetadataName,
                        operation.ValidatorType.MetadataName,
                    })
            .ToHashSet(StringComparer.Ordinal);
        MetadataTypeNameProvider provider = default;
        foreach (var handle in metadata.TypeDefinitions)
        {
            var type = metadata.GetTypeDefinition(handle);
            if (type.Attributes.HasFlag(TypeAttributes.Interface) ||
                type.Attributes.HasFlag(TypeAttributes.Abstract) ||
                !type.GetInterfaceImplementations().Any(implementation =>
                    contracts.Contains(
                        EntityType(
                            metadata,
                            metadata.GetInterfaceImplementation(
                                implementation).Interface,
                            provider))))
            {
                continue;
            }

            foreach (var methodHandle in type.GetMethods())
            {
                var method = metadata.GetMethodDefinition(methodHandle);
                if (metadata.GetString(method.Name) != ".ctor")
                {
                    continue;
                }

                var signature = method.DecodeSignature(provider, genericContext: null);
                if (signature.ParameterTypes.Any(IsForbiddenDependency))
                {
                    Error(
                        diagnostics,
                        "Consumer handler and validator constructors may not inject DI service locators, Spectre, or generated-host types.",
                        "/operations");
                }
            }
        }
    }

    private static bool IsForbiddenDependency(string metadataName) =>
        ForbiddenDependencies.Contains(metadataName) ||
        metadataName.StartsWith("Spectre.", StringComparison.Ordinal) ||
        metadataName.StartsWith("GeneratedHost.", StringComparison.Ordinal);

    private static string EntityType(
        MetadataReader metadata,
        EntityHandle handle,
        MetadataTypeNameProvider provider) =>
        handle.Kind == HandleKind.TypeSpecification
            ? metadata.GetTypeSpecification(
                    (TypeSpecificationHandle)handle)
                .DecodeSignature(provider, genericContext: null)
            : MetadataTypeNames.Entity(metadata, handle);

    private static bool HasPublicReadableProperty(
        MetadataReader metadata,
        TypeDefinition definition,
        string propertyName,
        string propertyType)
    {
        MetadataTypeNameProvider provider = default;
        foreach (var handle in definition.GetProperties())
        {
            var property = metadata.GetPropertyDefinition(handle);
            if (metadata.GetString(property.Name) != propertyName ||
                property.DecodeSignature(provider, genericContext: null)
                    .ReturnType != propertyType)
            {
                continue;
            }

            var getter = property.GetAccessors().Getter;
            return !getter.IsNil &&
                   metadata.GetMethodDefinition(getter)
                       .Attributes.HasFlag(MethodAttributes.Public);
        }

        return false;
    }

    private static bool HasPublicParameterlessConstructor(
        MetadataReader metadata,
        TypeDefinition definition)
    {
        MetadataTypeNameProvider provider = default;
        return definition.GetMethods()
            .Select(metadata.GetMethodDefinition)
            .Any(method =>
                metadata.GetString(method.Name) == ".ctor" &&
                method.Attributes.HasFlag(MethodAttributes.Public) &&
                !method.Attributes.HasFlag(MethodAttributes.Static) &&
                method.DecodeSignature(provider, genericContext: null)
                    .ParameterTypes.IsEmpty);
    }

    private static bool Implements(
        MetadataReader metadata,
        TypeDefinition definition,
        string interfaceName)
    {
        MetadataTypeNameProvider provider = default;
        return definition.GetInterfaceImplementations().Any(handle =>
            EntityType(
                metadata,
                metadata.GetInterfaceImplementation(handle).Interface,
                provider) == interfaceName);
    }

    private static bool TryType(
        DotNetConsoleClrTypeDescriptor descriptor,
        IReadOnlyDictionary<string, TypeDefinitionHandle> types,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        out TypeDefinitionHandle handle)
    {
        if (!types.TryGetValue(descriptor.MetadataName, out handle))
        {
            Error(
                diagnostics,
                "A CLR contract type named by the binding is missing from the exact consumer assembly.",
                path);
            return false;
        }

        return true;
    }

    private static bool IsPublic(TypeAttributes attributes) =>
        attributes.HasFlag(TypeAttributes.Public) ||
        attributes.HasFlag(TypeAttributes.NestedPublic);

    private static string Render(DotNetConsoleClrTypeDescriptor type) =>
        type.GenericArguments.IsEmpty
            ? type.MetadataName
            : string.Concat(
                type.MetadataName,
                "<",
                string.Join(",", type.GenericArguments.Select(Render)),
                ">");

    private static DotNetConsoleMetadataInspectionResult Invalid(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        new(false, null, diagnostics.ToImmutable());

    private static void Error(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string message,
        string path) =>
        diagnostics.Add(
            new ProgramKitDiagnostic(
                DotNetDiagnosticIds.ConsoleMetadataMismatch,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));
}
