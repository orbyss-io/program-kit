using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using SnapshotLesson;

/// <summary>Runs fixed independent expectations and a bounded local comparison.</summary>
internal static class Program
{
    /// <summary>Keeps measured results observable outside the timed delegates.</summary>
    private static long sink;

    /// <summary>Returns a failing exit for an oracle violation without launching a crash-reporting flow.</summary>
    private static int Main(string[] arguments)
    {
        try
        {
            Correctness();
            if (arguments.Contains("--benchmark")) Benchmark();
            return 0;
        }
        catch (InvalidOperationException error)
        {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
    }

    /// <summary>Exercises immutable ownership, exact identities, duplicates and the actual consumer report.</summary>
    private static void Correctness()
    {
        var one = new Note("n1", "alice");
        var other = new Note("secret", "bob");
        var two = new Note("n2", "alice");
        var upper = new Note("upper", "ALICE");
        var rows = new[] { one, other, one, two, upper };
        var query = new SnapshotQuery(rows);
        var scan = new SnapshotScan(rows);
        var application = new OwnerReport(rows);
        var expected = new[] { "n1", "n1", "n2" };
        var actual = query.ForOwner("alice");
        Equal(actual, expected);
        var baseline = scan.ForOwner("alice");
        Equal(baseline, expected);
        var applied = application.Rows("alice");
        Equal(applied, expected);
        var uppercase = query.ForOwner("ALICE");
        var uppercaseExpected = new[] { "upper" };
        Equal(uppercase, uppercaseExpected);
        var absent = query.ForOwner("nobody");
        var emptyExpected = Array.Empty<string>();
        Equal(absent, emptyExpected);
        var emptyRows = Array.Empty<Note>();
        var empty = new SnapshotQuery(emptyRows);
        var emptyResult = empty.ForOwner("alice");
        Equal(emptyResult, emptyExpected);
        rows[0] = other;
        var afterMutation = query.ForOwner("alice");
        Equal(afterMutation, expected);
        var mutable = actual as IList<Note>;
        if (mutable is not null)
        {
            var rejected = false;
            try { mutable[0] = other; }
            catch (NotSupportedException) { rejected = true; }
            Require(rejected, "caller-cannot-mutate-index-result");
        }
        // An old snapshot is intentionally not a live store. Rebuild for new input.
        var rebuilt = new SnapshotQuery(rows);
        var updated = rebuilt.ForOwner("alice");
        var updatedExpected = new[] { "n1", "n2" };
        Equal(updated, updatedExpected);
        var nullRejected = false;
        try { _ = new SnapshotQuery(null!); }
        catch (ArgumentNullException) { nullRejected = true; }
        Require(nullRejected, "null-input-admission");
        var nullOwnerRejected = false;
        try { _ = query.ForOwner(null!); }
        catch (ArgumentNullException) { nullOwnerRejected = true; }
        Require(nullOwnerRejected, "null-owner-admission");
        Console.WriteLine("PASS: owner isolation, exact case, stable order, duplicates, empty, snapshot copy, immutable output, rebuild, null admission and actual OwnerReport application.");
    }

    /// <summary>Compares owner results with independently authored expected identities and ordering.</summary>
    private static void Equal(IReadOnlyList<Note> rows, string[] expected)
    {
        var lengthMatches = rows.Count == expected.Length;
        Require(lengthMatches, "owner-isolation-and-duplicate-count");
        for (var index = 0; index < expected.Length; index++)
        {
            var matches = rows[index].Id == expected[index];
            Require(matches, "stable-owner-order");
        }
    }

    /// <summary>Rejects a failed fixed expectation with an authored assertion identity.</summary>
    private static void Require(bool value, string identity)
    {
        if (!value) throw new InvalidOperationException(identity);
    }

    /// <summary>Checks every workload row before recording repeated-query and preparation tradeoffs.</summary>
    private static void Benchmark()
    {
        var rows = Workload(8192);
        var index = new SnapshotQuery(rows);
        var scan = new SnapshotScan(rows);
        Func<string, IReadOnlyList<Note>> indexedQuery = index.ForOwner;
        Func<string, IReadOnlyList<Note>> scannedQuery = scan.ForOwner;
        for (var ownerNumber = 0; ownerNumber < 64; ownerNumber++)
        {
            var owner = "owner-" + ownerNumber;
            var expected = new string[128];
            for (var offset = 0; offset < expected.Length; offset++)
                expected[offset] = "note-" + (ownerNumber + offset * 64);
            var indexedRows = indexedQuery(owner);
            var scannedRows = scannedQuery(owner);
            Equal(indexedRows, expected);
            Equal(scannedRows, expected);
        }
        Exercise(indexedQuery, 256);
        Exercise(scannedQuery, 256);
        var samples = new List<object>();
        Action readIndex = () => Exercise(indexedQuery, 256);
        Action readScan = () => Exercise(scannedQuery, 256);
        Action buildIndex = () => { var value = new SnapshotQuery(rows); sink += value.ForOwner("owner-0").Count; };
        Action buildScan = () => { var value = new SnapshotScan(rows); sink += value.ForOwner("owner-0").Count; };
        buildIndex();
        buildScan();
        for (var round = 0; round < 5; round++)
        {
            // Alternate order to expose, rather than hide, warm/scheduling effects.
            var first = round % 2 == 0 ? Measure(readScan) : Measure(readIndex);
            var second = round % 2 == 0 ? Measure(readIndex) : Measure(readScan);
            var scanRead = round % 2 == 0 ? first : second;
            var indexedRead = round % 2 == 0 ? second : first;
            var indexBuildAndOne = Measure(buildIndex);
            var scanBuildAndOne = Measure(buildScan);
            samples.Add(new { round, scanRead, indexedRead, indexBuildAndOne, scanBuildAndOne });
        }
        var environment = new
        {
            runtime = RuntimeInformation.FrameworkDescription,
            os = RuntimeInformation.OSDescription,
            architecture = RuntimeInformation.ProcessArchitecture.ToString(),
            processors = Environment.ProcessorCount,
            configuration = "Release"
        };
        var result = new
        {
            environment, rows = 8192, owners = 64, lookups = 256, samples, sink,
            limits = "Local immutable snapshot only. Managed allocated bytes on this thread, not retained heap or process RSS. Construction allocates groups plus final arrays; one-shot scan remains an alternative. Rebuild after mutations. Remote storage remains unqualified; timings are local observations."
        };
        var json = JsonSerializer.Serialize(result);
        Console.WriteLine(json);
    }

    /// <summary>Builds the declared finite synthetic workload independently of the index.</summary>
    private static Note[] Workload(int count)
    {
        var rows = new Note[count];
        for (var index = 0; index < rows.Length; index++)
        {
            var id = "note-" + index;
            var owner = "owner-" + index % 64;
            rows[index] = new Note(id, owner);
        }
        return rows;
    }

    /// <summary>Consumes a fixed number of owner queries and preserves the results.</summary>
    private static void Exercise(Func<string, IReadOnlyList<Note>> query, int lookups)
    {
        for (var index = 0; index < lookups; index++)
        {
            var owner = "owner-" + index % 64;
            var rows = query(owner);
            sink += rows.Count;
        }
    }

    /// <summary>Records elapsed time and thread-local managed allocations for one workload.</summary>
    private static object Measure(Action work)
    {
        var before = GC.GetAllocatedBytesForCurrentThread();
        var clock = Stopwatch.StartNew();
        work();
        clock.Stop();
        var allocated = GC.GetAllocatedBytesForCurrentThread() - before;
        return new { milliseconds = clock.Elapsed.TotalMilliseconds, allocatedBytes = allocated };
    }


}
