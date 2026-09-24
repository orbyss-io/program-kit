namespace Lending.Core;

public enum ReservationState { Reserved, Confirmed, Cancelled }
public sealed record Reservation(string ReservationId, string OperationId, string EquipmentId, int Quantity, ReservationState State);
public sealed record Operation(string Fingerprint, Reservation Response);
public sealed class LendingState
{
    public int Available { get; set; } = 2;
    public Dictionary<string, Reservation> Reservations { get; set; } = [];
    public Dictionary<string, Operation> Operations { get; set; } = [];
    public int NotificationAttempts { get; set; }
    public int NotificationsSent { get; set; }
    public int PendingNotifications { get; set; }
    public bool FailNext { get; set; }
}
public interface ILendingStore
{
    T InTransaction<T>(Func<LendingState, T> operation);
}
public interface IReservationIdentity { string Next(); }
public enum Decision { Created, Replayed, Accepted, Invalid, Denied, DurablePending }
public sealed record Outcome(Decision Decision, Reservation? Reservation = null);
public static class ReservationPolicy
{
    public static bool CanReserve(string equipment, int quantity, int available) => equipment == "camera" && quantity > 0 && quantity <= available;
    public static bool CanTransition(ReservationState state) => state == ReservationState.Reserved;
}
public sealed class Reservations(ILendingStore store, IReservationIdentity identities)
{
    public Outcome Reserve(string operationId, string equipment, int quantity) => store.InTransaction(state =>
    {
        var fingerprint = $"reserve|{equipment}|{quantity}";
        if (Replay(state, operationId, fingerprint) is { } replay) return replay;
        if (!ReservationPolicy.CanReserve(equipment, quantity, state.Available)) return new Outcome(Decision.Denied);
        var reservation = new Reservation(identities.Next(), operationId, equipment, quantity, ReservationState.Reserved);
        state.Available -= quantity;
        state.Reservations.Add(reservation.ReservationId, reservation);
        state.Operations.Add(operationId, new(fingerprint, reservation));
        return new Outcome(Decision.Created, reservation);
    });
    public Outcome Transition(string id, string operationId, bool confirm, bool acknowledged) => store.InTransaction(state =>
    {
        if (confirm && !acknowledged) return new Outcome(Decision.Invalid);
        var fingerprint = $"transition|{id}|{confirm}|{acknowledged}";
        if (Replay(state, operationId, fingerprint) is { } replay) return replay;
        if (!state.Reservations.TryGetValue(id, out var current) || !ReservationPolicy.CanTransition(current.State)) return new Outcome(Decision.Denied);
        var updated = current with { State = confirm ? ReservationState.Confirmed : ReservationState.Cancelled };
        state.Reservations[id] = updated;
        var decision = Decision.Accepted;
        if (!confirm) state.Available += current.Quantity;
        else
        {
            // The fictional notification adapter is a durable deterministic sink;
            // this does not claim distributed exactly-once delivery in production.
            state.NotificationAttempts++;
            if (state.FailNext) { state.FailNext = false; state.PendingNotifications++; decision = Decision.DurablePending; }
            else state.NotificationsSent++;
        }
        state.Operations.Add(operationId, new(fingerprint, updated));
        return new Outcome(decision, updated);
    });
    private static Outcome? Replay(LendingState state, string id, string fingerprint) =>
        state.Operations.TryGetValue(id, out var previous)
            ? previous.Fingerprint == fingerprint ? new(Decision.Replayed, previous.Response) : new(Decision.Denied)
            : null;
}
