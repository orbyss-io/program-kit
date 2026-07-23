using System.Reflection;
using System.Reflection.Emit;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal static class ForeignOriginContextEmitter
{
    private static readonly Lazy<Type> EmittedContextType = new(EmitContextType);

    internal static JsonSerializerContext Create(
        JsonSerializerContext inner)
    {
        ArgumentNullException.ThrowIfNull(inner);
        var instance = Activator.CreateInstance(
            EmittedContextType.Value,
            inner,
            new JsonSerializerOptions());
        return instance as JsonSerializerContext
            ?? throw new InvalidOperationException(
                "The emitted foreign-origin context could not be created.");
    }

    private static Type EmitContextType()
    {
        var assemblyName = new AssemblyName(
            "Orbyss.ProgramKit.UnitTests.ForeignOriginContext");
        var assembly = AssemblyBuilder.DefineDynamicAssembly(
            assemblyName,
            AssemblyBuilderAccess.Run);
        var module = assembly.DefineDynamicModule(assemblyName.Name!);
        var typeBuilder = module.DefineType(
            "Orbyss.ProgramKit.UnitTests.Dynamic.ForeignOriginJsonContext",
            TypeAttributes.Public |
            TypeAttributes.Sealed |
            TypeAttributes.Class,
            typeof(JsonSerializerContext));

        var serializableConstructor =
            typeof(JsonSerializableAttribute).GetConstructor([typeof(Type)])
            ?? throw new InvalidOperationException(
                "JsonSerializableAttribute(Type) is unavailable.");
        var serializableAttribute = new CustomAttributeBuilder(
            serializableConstructor,
            [typeof(string)]);
        typeBuilder.SetCustomAttribute(serializableAttribute);

        var innerField = typeBuilder.DefineField(
            "inner",
            typeof(JsonSerializerContext),
            FieldAttributes.Private |
            FieldAttributes.InitOnly);
        var baseConstructor =
            typeof(JsonSerializerContext).GetConstructor(
                BindingFlags.Instance | BindingFlags.NonPublic,
                binder: null,
                [typeof(JsonSerializerOptions)],
                modifiers: null)
            ?? throw new InvalidOperationException(
                "The JSON context constructor is unavailable.");
        var constructor = typeBuilder.DefineConstructor(
            MethodAttributes.Public,
            CallingConventions.Standard,
            [typeof(JsonSerializerContext), typeof(JsonSerializerOptions)]);
        var constructorIl = constructor.GetILGenerator();
        constructorIl.Emit(OpCodes.Ldarg_0);
        constructorIl.Emit(OpCodes.Ldarg_2);
        constructorIl.Emit(OpCodes.Call, baseConstructor);
        constructorIl.Emit(OpCodes.Ldarg_0);
        constructorIl.Emit(OpCodes.Ldarg_1);
        constructorIl.Emit(OpCodes.Stfld, innerField);
        constructorIl.Emit(OpCodes.Ret);

        ImplementGeneratedOptions(typeBuilder);

        var baseGetTypeInfo = typeof(JsonSerializerContext).GetMethod(
            nameof(JsonSerializerContext.GetTypeInfo),
            [typeof(Type)])
            ?? throw new InvalidOperationException(
                "JsonSerializerContext.GetTypeInfo(Type) is unavailable.");
        var getTypeInfo = typeBuilder.DefineMethod(
            nameof(JsonSerializerContext.GetTypeInfo),
            MethodAttributes.Public |
            MethodAttributes.Virtual |
            MethodAttributes.HideBySig,
            typeof(JsonTypeInfo),
            [typeof(Type)]);
        var getTypeInfoIl = getTypeInfo.GetILGenerator();
        getTypeInfoIl.Emit(OpCodes.Ldarg_0);
        getTypeInfoIl.Emit(OpCodes.Ldfld, innerField);
        getTypeInfoIl.Emit(OpCodes.Ldarg_1);
        getTypeInfoIl.Emit(OpCodes.Callvirt, baseGetTypeInfo);
        getTypeInfoIl.Emit(OpCodes.Ret);
        typeBuilder.DefineMethodOverride(getTypeInfo, baseGetTypeInfo);

        return typeBuilder.CreateType()
            ?? throw new InvalidOperationException(
                "The foreign-origin context type could not be emitted.");
    }

    private static void ImplementGeneratedOptions(TypeBuilder typeBuilder)
    {
        var baseGetter = typeof(JsonSerializerContext)
            .GetProperty(
                "GeneratedSerializerOptions",
                BindingFlags.Instance | BindingFlags.NonPublic)
            ?.GetMethod
            ?? throw new InvalidOperationException(
                "The generated-options contract is unavailable.");
        var getter = typeBuilder.DefineMethod(
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
        typeBuilder.DefineMethodOverride(getter, baseGetter);
    }
}
