using Lending.Core;
using Lending.Storage;
using Microsoft.Extensions.DependencyInjection;
using System.Xml.Linq;
var suite = new XElement("testsuite", new XAttribute("name", "ReferenceExtensions"));
var failed = false;
Run("core-dependencies", () =>
{
    var forbidden = new[] { "Lending.Storage", "Microsoft.AspNetCore", "Microsoft.Extensions", "System.Text.Json" };
    Require(!typeof(Reservations).Assembly.GetReferencedAssemblies().Any(a => forbidden.Any(p => a.Name!.StartsWith(p, StringComparison.Ordinal))), "Core leaks adapter dependencies");
});
Run("runtime-resolution-and-replacement", () =>
{
    foreach (var store in new ILendingStore[] { new MemoryStore(), new FileLendingStore(Path.Combine(Directory.GetCurrentDirectory(), "adapter-data")) })
    {
        var identities = new SequenceIdentity();
        using var services = new ServiceCollection().AddSingleton(store).AddSingleton<ILendingStore>(store)
            .AddSingleton<IReservationIdentity>(identities).AddSingleton<Reservations>().BuildServiceProvider(new ServiceProviderOptions { ValidateOnBuild = true, ValidateScopes = true });
        var reservations = services.GetRequiredService<Reservations>();
        Require(reservations.Reserve("denied", "camera", 3).Decision == Decision.Denied && identities.Count == 0, "Denied policy invoked identity/effect port");
        var accepted = reservations.Reserve("reserve", "camera", 1);
        Require(accepted.Decision == Decision.Created, "Replacement cannot reserve");
        Require(reservations.Reserve("reserve", "camera", 1).Reservation == accepted.Reservation && identities.Count == 1, "Replacement lost idempotent identity");
        Require(reservations.Transition(accepted.Reservation!.ReservationId, "confirm", true, false).Decision == Decision.Invalid, "Replacement accepted absent acknowledgement");
        Require(reservations.Transition(accepted.Reservation.ReservationId, "cancel", false, true).Decision == Decision.Accepted, "Replacement cannot cancel");
        Require(reservations.Transition(accepted.Reservation.ReservationId, "illegal", true, true).Decision == Decision.Denied, "Replacement allowed terminal transition");
        Require(store.InTransaction(s => s.Available == 2 && s.NotificationsSent == 0 && s.NotificationAttempts == 0), "Replacement changed effect invariants");
    }
});
new XDocument(suite).Save("results.xml");
return failed ? 1 : 0;
void Run(string name, Action test) { var item = new XElement("testcase", new XAttribute("classname", "ReferenceExtensions"), new XAttribute("name", name)); suite.Add(item); try { test(); } catch (Exception e) { failed = true; item.Add(new XElement("failure", e.ToString())); } }
static void Require(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
sealed class SequenceIdentity : IReservationIdentity { public int Count { get; private set; } public string Next() => "reference-" + ++Count; }
sealed class MemoryStore : ILendingStore { private readonly LendingState state = new(); public T InTransaction<T>(Func<LendingState,T> operation) => operation(state); }
