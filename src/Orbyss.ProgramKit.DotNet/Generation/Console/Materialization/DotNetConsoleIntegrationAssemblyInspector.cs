using System.Buffers.Binary;
using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Offline verifier for the single-project Console contract and implementation
/// seam.
/// </summary>
public sealed class DotNetConsoleIntegrationAssemblyInspector :
    IDotNetConsoleIntegrationAssemblyInspector
{
    private static readonly Dictionary<ushort, OperandType>
        OperandTypes = CreateOperandTypes();

    /// <inheritdoc />
    public ProgramKitValidationResult Inspect(
        DotNetConsoleBindingDocument binding,
        string referenceAssemblyPath)
    {
        ArgumentNullException.ThrowIfNull(binding);
        ArgumentException.ThrowIfNullOrWhiteSpace(referenceAssemblyPath);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        try
        {
            using FileStream stream = new(
                referenceAssemblyPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read);
            using PEReader peReader = new(stream);
            if (!peReader.HasMetadata)
            {
                Error(
                    diagnostics,
                    "The selected Console integration reference is not a managed assembly.");
                return ProgramKitValidationResult.From(diagnostics);
            }

            var metadata = peReader.GetMetadataReader();
            var contracts = binding.Operations
                .SelectMany(static operation =>
                    operation.ValidatorType is null
                        ? ImmutableArray.Create(
                            operation.HandlerType.MetadataName)
                        : ImmutableArray.Create(
                            operation.HandlerType.MetadataName,
                            operation.ValidatorType.MetadataName))
                .Distinct(StringComparer.Ordinal)
                .ToArray();
            Dictionary<string, string> implementations =
                new(StringComparer.Ordinal);
            foreach (var contract in contracts)
            {
                var candidates = Implementations(
                    metadata,
                    contract);
                if (candidates.Length != 1)
                {
                    Error(
                        diagnostics,
                        string.Concat(
                            "The selected Console integration assembly must contain exactly one public sealed concrete implementation of ",
                            contract,
                            "."));
                    continue;
                }

                implementations.Add(contract, candidates[0]);
            }

            VerifyRegistrations(
                peReader,
                metadata,
                binding,
                implementations,
                diagnostics);
        }
        catch (Exception exception) when (
            exception is BadImageFormatException or
                IOException or
                UnauthorizedAccessException)
        {
            Error(
                diagnostics,
                "The selected Console integration reference assembly is unreadable.");
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void VerifyRegistrations(
        PEReader peReader,
        MetadataReader metadata,
        DotNetConsoleBindingDocument binding,
        IReadOnlyDictionary<string, string> implementations,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var featureHandles = metadata.TypeDefinitions
            .Where(handle => string.Equals(
                MetadataTypeNames.Definition(metadata, handle),
                binding.FeatureType.MetadataName,
                StringComparison.Ordinal))
            .ToArray();
        if (featureHandles.Length != 1)
        {
            return;
        }

        var feature = metadata.GetTypeDefinition(featureHandles[0]);
        var methods = feature.GetMethods()
            .Select(metadata.GetMethodDefinition)
            .Where(method =>
                metadata.GetString(method.Name) == "ConfigureServices" &&
                method.Attributes.HasFlag(MethodAttributes.Public) &&
                !method.Attributes.HasFlag(MethodAttributes.Static))
            .ToArray();
        if (methods.Length != 1 ||
            methods[0].RelativeVirtualAddress == 0)
        {
            Error(
                diagnostics,
                "The selected Console feature must own one public instance ConfigureServices implementation.");
            return;
        }

        ImmutableArray<ConsoleServiceRegistration> registrations;
        try
        {
            var body = peReader.GetMethodBody(
                methods[0].RelativeVirtualAddress);
            var il = body.GetILBytes() ??
                throw new BadImageFormatException(
                    "The selected Console feature has no method body.");
            registrations = ReadRegistrations(
                metadata,
                il);
        }
        catch (BadImageFormatException)
        {
            Error(
                diagnostics,
                "The selected Console feature has invalid registration IL.");
            return;
        }

        if (registrations.Any(registration => string.Equals(
                registration.ServiceType,
                "CShells.Features.IShellFeature",
                StringComparison.Ordinal)))
        {
            Error(
                diagnostics,
                "The selected Console feature must not register IShellFeature.");
        }

        foreach (var operation in binding.Operations)
        {
            VerifyRegistration(
                operation.HandlerType.MetadataName,
                required: true,
                implementations,
                registrations,
                diagnostics);
            if (operation.ValidatorType is not null)
            {
                VerifyRegistration(
                    operation.ValidatorType.MetadataName,
                    required: false,
                    implementations,
                    registrations,
                    diagnostics);
            }
        }
    }

    private static void VerifyRegistration(
        string contract,
        bool required,
        IReadOnlyDictionary<string, string> implementations,
        ImmutableArray<ConsoleServiceRegistration> registrations,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var matches = registrations
            .Where(registration => string.Equals(
                registration.ServiceType,
                contract,
                StringComparison.Ordinal))
            .ToArray();
        var expectedCount = required ? 1 : Math.Min(matches.Length, 1);
        if (matches.Length != expectedCount ||
            !implementations.TryGetValue(contract, out var implementation) ||
            matches.Any(registration => !string.Equals(
                registration.ImplementationType,
                implementation,
                StringComparison.Ordinal)))
        {
            Error(
                diagnostics,
                string.Concat(
                    required ? "Handler " : "Validator ",
                    contract,
                    required
                        ? " must have exactly one direct unkeyed scoped service-to-implementation registration."
                        : " may have at most one direct unkeyed scoped service-to-implementation registration using its exact implementation."));
        }
    }

    private static ImmutableArray<ConsoleServiceRegistration>
        ReadRegistrations(
            MetadataReader metadata,
            byte[] il)
    {
        var registrations =
            ImmutableArray.CreateBuilder<ConsoleServiceRegistration>();
        var offset = 0;
        while (offset < il.Length)
        {
            var opcode = ReadOpcode(il, ref offset);
            var operandOffset = offset;
            var operandSize = OperandSize(
                opcode,
                il,
                operandOffset);
            if (operandOffset + operandSize > il.Length)
            {
                throw new BadImageFormatException(
                    "A Console feature instruction operand is truncated.");
            }

            if (opcode == unchecked((ushort)OpCodes.Call.Value) &&
                operandSize == sizeof(int))
            {
                var token = BinaryPrimitives.ReadInt32LittleEndian(
                    il.AsSpan(operandOffset, sizeof(int)));
                var registration = Registration(metadata, token);
                if (registration is not null)
                {
                    registrations.Add(registration);
                }
            }

            offset += operandSize;
        }

        return registrations.ToImmutable();
    }

    private static ConsoleServiceRegistration? Registration(
        MetadataReader metadata,
        int token)
    {
        var handle = MetadataTokens.EntityHandle(token);
        if (handle.Kind != HandleKind.MethodSpecification)
        {
            return null;
        }

        var specification = metadata.GetMethodSpecification(
            (MethodSpecificationHandle)handle);
        if (specification.Method.Kind != HandleKind.MemberReference)
        {
            return null;
        }

        var member = metadata.GetMemberReference(
            (MemberReferenceHandle)specification.Method);
        if (!string.Equals(
                metadata.GetString(member.Name),
                "AddScoped",
                StringComparison.Ordinal) ||
            !string.Equals(
                MetadataTypeNames.Entity(metadata, member.Parent),
                "Microsoft.Extensions.DependencyInjection.ServiceCollectionServiceExtensions",
                StringComparison.Ordinal))
        {
            return null;
        }

        MetadataTypeNameProvider provider = default;
        var arguments = specification.DecodeSignature(
            provider,
            genericContext: null);
        return arguments.Length == 2
            ? new ConsoleServiceRegistration(
                arguments[0],
                arguments[1])
            : null;
    }

    private static ushort ReadOpcode(byte[] il, ref int offset)
    {
        var first = il[offset++];
        if (first != 0xfe)
        {
            return first;
        }

        if (offset >= il.Length)
        {
            throw new BadImageFormatException(
                "A Console feature instruction opcode is truncated.");
        }

        return (ushort)(0xfe00 | il[offset++]);
    }

    private static int OperandSize(
        ushort opcode,
        byte[] il,
        int operandOffset)
    {
        if (!OperandTypes.TryGetValue(opcode, out var operandType))
        {
            throw new BadImageFormatException(
                "A Console feature instruction opcode is unsupported.");
        }

        return operandType switch
        {
            OperandType.InlineNone => 0,
            OperandType.ShortInlineBrTarget or
            OperandType.ShortInlineI or
            OperandType.ShortInlineVar => 1,
            OperandType.InlineVar => 2,
            OperandType.InlineBrTarget or
            OperandType.InlineField or
            OperandType.InlineI or
            OperandType.InlineMethod or
            OperandType.InlineSig or
            OperandType.InlineString or
            OperandType.InlineTok or
            OperandType.InlineType or
            OperandType.ShortInlineR => 4,
            OperandType.InlineI8 or
            OperandType.InlineR => 8,
            OperandType.InlineSwitch => SwitchOperandSize(
                il,
                operandOffset),
            _ => throw new BadImageFormatException(
                "A Console feature instruction operand is unsupported."),
        };
    }

    private static int SwitchOperandSize(byte[] il, int operandOffset)
    {
        if (operandOffset + sizeof(int) > il.Length)
        {
            throw new BadImageFormatException(
                "A Console feature switch operand is truncated.");
        }

        var count = BinaryPrimitives.ReadInt32LittleEndian(
            il.AsSpan(operandOffset, sizeof(int)));
        if (count < 0 ||
            count > (il.Length - operandOffset - sizeof(int)) / sizeof(int))
        {
            throw new BadImageFormatException(
                "A Console feature switch operand is invalid.");
        }

        return checked(sizeof(int) + (count * sizeof(int)));
    }

    private static Dictionary<ushort, OperandType>
        CreateOperandTypes()
    {
        Dictionary<ushort, OperandType> result = [];
        foreach (var field in typeof(OpCodes).GetFields(
                     BindingFlags.Public | BindingFlags.Static))
        {
            if (field.GetValue(null) is OpCode opcode)
            {
                result.Add(
                    unchecked((ushort)opcode.Value),
                    opcode.OperandType);
            }
        }

        return result;
    }

    private static ImmutableArray<string> Implementations(
        MetadataReader metadata,
        string contract)
    {
        MetadataTypeNameProvider provider = default;
        return metadata.TypeDefinitions
            .Select(handle => (
                Handle: handle,
                Definition: metadata.GetTypeDefinition(handle)))
            .Where(item =>
                IsPublic(item.Definition.Attributes) &&
                item.Definition.Attributes.HasFlag(TypeAttributes.Sealed) &&
                !item.Definition.Attributes.HasFlag(TypeAttributes.Abstract) &&
                !item.Definition.Attributes.HasFlag(TypeAttributes.Interface) &&
                item.Definition.GetGenericParameters().Count == 0 &&
                item.Definition.GetInterfaceImplementations().Any(
                    implementation =>
                        EntityType(
                            metadata,
                            metadata.GetInterfaceImplementation(
                                implementation).Interface,
                            provider) == contract))
            .Select(item => MetadataTypeNames.Definition(
                metadata,
                item.Handle))
            .Order(StringComparer.Ordinal)
            .ToImmutableArray();
    }

    private static string EntityType(
        MetadataReader metadata,
        EntityHandle handle,
        MetadataTypeNameProvider provider) =>
        handle.Kind == HandleKind.TypeSpecification
            ? metadata.GetTypeSpecification(
                    (TypeSpecificationHandle)handle)
                .DecodeSignature(provider, genericContext: null)
            : MetadataTypeNames.Entity(metadata, handle);

    private static bool IsPublic(TypeAttributes attributes) =>
        attributes.HasFlag(TypeAttributes.Public) ||
        attributes.HasFlag(TypeAttributes.NestedPublic);

    private static void Error(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string message) =>
        diagnostics.Add(
            new ProgramKitDiagnostic(
                DotNetDiagnosticIds.ConsoleMetadataMismatch,
                ProgramKitDiagnosticSeverity.Error,
                message,
                "/consumerProject"));
}
