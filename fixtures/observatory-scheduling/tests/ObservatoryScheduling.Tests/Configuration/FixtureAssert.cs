using Orbyss.ProgramKit.Artifacts.Validation;

namespace ObservatoryScheduling.Tests.Configuration;

internal static class FixtureAssert
{
    internal static void AreEqual<T>(T expected, T actual)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new InvalidOperationException(
                $"Expected '{expected}', but observed '{actual}'.");
        }
    }

    internal static void HasCount<T>(int expected, IReadOnlyCollection<T> actual)
    {
        ArgumentNullException.ThrowIfNull(actual);
        AreEqual(expected, actual.Count);
    }

    internal static void IsFalse(bool condition)
    {
        if (condition)
        {
            throw new InvalidOperationException("Expected false.");
        }
    }

    internal static void IsTrue(bool condition)
    {
        if (!condition)
        {
            throw new InvalidOperationException("Expected true.");
        }
    }

    internal static void IsValid(ProgramKitValidationResult result)
    {
        ArgumentNullException.ThrowIfNull(result);
        if (!result.IsValid)
        {
            throw new InvalidOperationException(
                string.Join(
                    Environment.NewLine,
                    result.Diagnostics.Select(static diagnostic =>
                        string.Concat(
                            diagnostic.Id,
                            " ",
                            diagnostic.Path,
                            ": ",
                            diagnostic.Message))));
        }
    }

    internal static void IsNotNull<T>(T? value)
    {
        if (value is null)
        {
            throw new InvalidOperationException("Expected a non-null value.");
        }
    }

    internal static void IsNull<T>(T? value)
    {
        if (value is not null)
        {
            throw new InvalidOperationException("Expected a null value.");
        }
    }

    internal static void IsType<T>(object value)
    {
        if (value is not T)
        {
            throw new InvalidOperationException(
                $"Expected an implementation of {typeof(T).FullName}.");
        }
    }

    internal static void SequenceEqual(
        ReadOnlySpan<byte> expected,
        ReadOnlySpan<byte> actual)
    {
        if (!expected.SequenceEqual(actual))
        {
            throw new InvalidOperationException(
                "Expected byte sequences to be identical.");
        }
    }

    internal static async Task ThrowsExactlyAsync<TException>(
        Func<Task> action)
        where TException : Exception
    {
        ArgumentNullException.ThrowIfNull(action);
        try
        {
            await action();
        }
        catch (TException exception)
            when (exception.GetType() == typeof(TException))
        {
            return;
        }

        throw new InvalidOperationException(
            $"Expected {typeof(TException).FullName}.");
    }
}
