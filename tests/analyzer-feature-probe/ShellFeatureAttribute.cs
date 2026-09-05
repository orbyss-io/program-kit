namespace CShells.Features;

/// <summary>Minimal analyzer-probe feature attribute.</summary>
/// <param name="name">The runtime feature identity.</param>
[AttributeUsage(AttributeTargets.Class)]
public sealed class ShellFeatureAttribute(string name) : Attribute
{
    /// <summary>Gets the runtime feature identity.</summary>
    public string Name { get; } = name;
}
