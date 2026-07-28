using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;

namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Build.Composition;

internal static class GeneratedOutputIntegrityBuildComposition
{
    internal static IGeneratedOutputIntegrityVerifier CreateVerifier() =>
        new GeneratedOutputIntegrityVerifier();
}
