using ProgramKit.Examples.Evidence;

namespace Evidence.Probe;

/// <summary>Pure application-client substitution; no persistence, HTTP or durable-effect claim.</summary>
internal static class ApplicationContractChecks
{
    internal static async Task VerifyAsync()
    {
        var journal = new ObservationJournal();
        IEvidenceSubmissions application = new EvidenceSubmissions(journal);
        var bytes = System.Text.Encoding.UTF8.GetBytes("fictional client substitution");
        var date = new DateOnly(
            2026,
            10,
            18
        );
        var packet = EvidencePacket.Create(
            "Application contract",
            date,
            bytes
        );
        foreach (var action in new Func<Task>[]
        {
            () => application.PrepareAsync(
                "",
                packet,
                CancellationToken.None
            ),
            () => application.AcceptAsync(
                "reviewer",
                "invalid identity",
                CancellationToken.None
            )
        })
        {
            try { await action(); throw new Exception("invalid business admission reached provider"); }
            catch (ArgumentException) { }
        }
        using var cancelled = new CancellationTokenSource();
        cancelled.Cancel();
        try
        {
            await application.PrepareAsync(
                "reviewer",
                packet,
                cancelled.Token
            );
            throw new Exception("cancelled preparation reached provider");
        }
        catch (OperationCanceledException) { }
        if (journal.Calls != 0) throw new Exception("admission allocated a provider effect");
        var prepared = await application.PrepareAsync(
            "reviewer",
            packet,
            CancellationToken.None
        );
        var observed = await application.FindAsync(
            "reviewer",
            prepared.Id,
            CancellationToken.None
        );
        if (prepared.Accepted || observed != prepared || journal.Calls != 2)
            throw new Exception("application client contract differs across journal substitutions");
        var accepted = await application.AcceptAsync(
            "reviewer",
            prepared.Id,
            CancellationToken.None
        );
        if (accepted?.Accepted != true || accepted.Id != prepared.Id)
            throw new Exception("application acceptance contract differs across journal substitutions");
    }

    private sealed class ObservationJournal : IEvidenceJournal
    {
        internal int Calls { get; private set; }
        private EvidenceReceipt? observation;
        private string? admittedOwner;

        public Task<EvidenceReceipt> PrepareAsync(
            string owner,
            EvidencePacket packet,
            CancellationToken cancellation
        )
        {
            Calls++;
            var identity = Guid.NewGuid();
            var id = identity.ToString("N");
            admittedOwner = owner;
            observation = new EvidenceReceipt(
                id,
                packet.Title,
                packet.Date,
                packet.Hash,
                false
            );
            return Task.FromResult(observation);
        }

        public Task<EvidenceReceipt?> AcceptAsync(
            string owner,
            string identity,
            CancellationToken cancellation
        )
        {
            Calls++;
            if (admittedOwner != owner || observation?.Id != identity)
                return Task.FromResult<EvidenceReceipt?>(null);
            observation = observation with { Accepted = true };
            return Task.FromResult<EvidenceReceipt?>(observation);
        }

        public Task<EvidenceReceipt?> FindAsync(
            string owner,
            string identity,
            CancellationToken cancellation
        )
        {
            Calls++;
            var result = admittedOwner == owner && observation?.Id == identity ? observation : null;
            return Task.FromResult(result);
        }
    }
}
