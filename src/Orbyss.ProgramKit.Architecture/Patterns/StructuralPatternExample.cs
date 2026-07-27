using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Patterns;

/// <summary>A bounded illustration of a structural pattern.</summary>
public sealed record StructuralPatternExample(
    string Name,
    string Context,
    string Application,
    string Consequence);
