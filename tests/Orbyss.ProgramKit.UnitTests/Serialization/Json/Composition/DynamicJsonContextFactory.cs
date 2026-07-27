using System.Reflection;
using System.Reflection.Emit;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal static class DynamicJsonContextFactory
{
    internal static JsonSerializerContext Create(Type target)
    {
        var assemblyName = new AssemblyName(
            string.Concat(
                "ProgramKitJsonContextProbe_",
                Guid.NewGuid().ToString("N")));
        var assembly = AssemblyBuilder.DefineDynamicAssembly(
            assemblyName,
            AssemblyBuilderAccess.Run);
        var module = assembly.DefineDynamicModule(assemblyName.Name!);
        var contextType = module.DefineType(
            string.Concat(
                "ProgramKitJsonContextProbe_",
                Guid.NewGuid().ToString("N")),
            TypeAttributes.Public | TypeAttributes.Sealed,
            typeof(JsonSerializerContext));
        AddSerializableTarget(contextType, target);
        ImplementConstructor(contextType);
        ImplementGeneratedOptions(contextType);
        ImplementTypeInfoResolver(contextType);
        var createdType = contextType.CreateType()
            ?? throw new InvalidOperationException(
                "The dynamic JSON context type was not created.");
        return (JsonSerializerContext)Activator.CreateInstance(
            createdType,
            new JsonSerializerOptions())!;
    }

    private static void AddSerializableTarget(
        TypeBuilder contextType,
        Type target)
    {
        var constructor = typeof(JsonSerializableAttribute).GetConstructor(
            [typeof(Type)])
            ?? throw new InvalidOperationException(
                "The JSON serializable attribute constructor is unavailable.");
        contextType.SetCustomAttribute(
            new CustomAttributeBuilder(constructor, [target]));
    }

    private static void ImplementConstructor(TypeBuilder contextType)
    {
        var baseConstructor = typeof(JsonSerializerContext).GetConstructor(
            BindingFlags.Instance | BindingFlags.NonPublic,
            binder: null,
            [typeof(JsonSerializerOptions)],
            modifiers: null)
            ?? throw new InvalidOperationException(
                "The JSON context constructor is unavailable.");
        var constructor = contextType.DefineConstructor(
            MethodAttributes.Public,
            CallingConventions.Standard,
            [typeof(JsonSerializerOptions)]);
        var generator = constructor.GetILGenerator();
        generator.Emit(OpCodes.Ldarg_0);
        generator.Emit(OpCodes.Ldarg_1);
        generator.Emit(OpCodes.Call, baseConstructor);
        generator.Emit(OpCodes.Ret);
    }

    private static void ImplementGeneratedOptions(TypeBuilder contextType)
    {
        var baseGetter = typeof(JsonSerializerContext)
            .GetProperty(
                "GeneratedSerializerOptions",
                BindingFlags.Instance | BindingFlags.NonPublic)
            ?.GetMethod
            ?? throw new InvalidOperationException(
                "The generated-options contract is unavailable.");
        var getter = contextType.DefineMethod(
            baseGetter.Name,
            MethodAttributes.Family |
            MethodAttributes.Virtual |
            MethodAttributes.HideBySig |
            MethodAttributes.SpecialName,
            typeof(JsonSerializerOptions),
            Type.EmptyTypes);
        var generator = getter.GetILGenerator();
        generator.Emit(OpCodes.Ldnull);
        generator.Emit(OpCodes.Ret);
        contextType.DefineMethodOverride(getter, baseGetter);
    }

    private static void ImplementTypeInfoResolver(TypeBuilder contextType)
    {
        var baseMethod = typeof(JsonSerializerContext).GetMethod(
            nameof(JsonSerializerContext.GetTypeInfo),
            [typeof(Type)])
            ?? throw new InvalidOperationException(
                "The JSON type-info contract is unavailable.");
        var method = contextType.DefineMethod(
            baseMethod.Name,
            MethodAttributes.Public |
            MethodAttributes.Virtual |
            MethodAttributes.HideBySig,
            typeof(JsonTypeInfo),
            [typeof(Type)]);
        var generator = method.GetILGenerator();
        generator.Emit(OpCodes.Ldnull);
        generator.Emit(OpCodes.Ret);
        contextType.DefineMethodOverride(method, baseMethod);
    }
}
