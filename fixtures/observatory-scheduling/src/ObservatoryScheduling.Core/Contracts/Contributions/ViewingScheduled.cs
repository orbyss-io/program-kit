using Orbyss.ProgramKit.Modularity.Contributions;
using ObservatoryScheduling.Core.Contracts.Scheduling;

namespace ObservatoryScheduling.Core.Contracts.Contributions;

/// <summary>Event-like fictional fact emitted after a viewing session is selected.</summary>
public sealed record ViewingScheduled(ViewingSession Session) : IDomainContribution;
