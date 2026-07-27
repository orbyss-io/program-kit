namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.WrappedInterfaceInitializerDependency;

internal sealed class WrappedInterfaceInitializerDependency
{
    internal Func<IWrappedInitializerValidator> CreateValidator { get; } =
        ResolveValidatorFactory();

    private static Func<IWrappedInitializerValidator>
        ResolveValidatorFactory() =>
        throw new NotSupportedException();
}
