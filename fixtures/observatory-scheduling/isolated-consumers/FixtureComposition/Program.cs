using CShells.Features;
using ObservatoryScheduling.Constraints.DarknessWindow.Features;
using ObservatoryScheduling.Scheduling.FirstAvailable.Features;
using ObservatoryScheduling.Visibility.Fixed.Features;

namespace ProgramKit.IsolatedConsumers.FixtureComposition;

internal static class Program
{
    private static int Main()
    {
        var features = new[]
        {
            typeof(DarknessWindowFeature),
            typeof(FirstAvailableFeature),
            typeof(StaticVisibilityFeature),
        };
        return features.All(static feature =>
            typeof(IShellFeature).IsAssignableFrom(feature))
                ? 0
                : 1;
    }
}
