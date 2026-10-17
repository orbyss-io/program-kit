export interface ProgramKitSessionPolicy {
  idleMinutes: number;
  absoluteMinutes: number;
  absoluteDeadlineClaim: 'auth_time';
  tokenExpiryClaim: 'exp';
  crossTabCoordination: 'required-no-token-payload';
  providerLogoutFailure: 'local-session-remains-cleared';
}

export interface ProgramKitSessionState {
  nowSeconds: number;
  authTimeSeconds: number;
  tokenExpiresAtSeconds: number;
  lastActivityAtSeconds: number;
}

export type ProgramKitSessionDecision =
  | { active: true; expiresAtSeconds: number }
  | { active: false; reason: 'absolute-expiry' | 'idle-expiry' | 'token-expiry' };

export function evaluateProgramKitSession(
  policy: ProgramKitSessionPolicy,
  state: ProgramKitSessionState,
): ProgramKitSessionDecision {
  const absoluteExpiry = state.authTimeSeconds + policy.absoluteMinutes * 60;
  const idleExpiry = state.lastActivityAtSeconds + policy.idleMinutes * 60;
  if (state.nowSeconds >= absoluteExpiry) return { active: false, reason: 'absolute-expiry' };
  if (state.nowSeconds >= idleExpiry) return { active: false, reason: 'idle-expiry' };
  if (state.nowSeconds >= state.tokenExpiresAtSeconds) return { active: false, reason: 'token-expiry' };
  return { active: true, expiresAtSeconds: Math.min(absoluteExpiry, idleExpiry, state.tokenExpiresAtSeconds) };
}

export async function localFirstProgramKitLogout(
  clearLocalAuthentication: () => void | Promise<void>,
  beginProviderLogout: () => void | Promise<void>,
): Promise<'provider-started' | 'provider-unavailable'> {
  // Private state and the selected client's memory store must be cleared in this
  // event stack. Awaiting even an already resolved promise loses the popup gesture.
  // Full confirmation/session controls belong to the selected Foundation module.
  const cleared = clearLocalAuthentication();
  if (cleared && typeof cleared.then === 'function') {
    // Observe rejection without treating an asynchronous clear as completed.
    void cleared.catch(() => undefined);
    throw new Error('PKW107 SPA logout requires synchronous local authentication clearing.');
  }
  try {
    await beginProviderLogout();
    return 'provider-started';
  } catch {
    return 'provider-unavailable';
  }
}

export function createProgramKitLogoutChannel(
  onRemoteSignOut: () => void,
  channelName = 'program-kit-auth',
): { announceSignOut: () => void; close: () => void } {
  const channel = new BroadcastChannel(channelName);
  channel.addEventListener('message', (event: MessageEvent<unknown>) => {
    if (event.data === 'signed-out') onRemoteSignOut();
  });
  return {
    announceSignOut: () => channel.postMessage('signed-out'),
    close: () => channel.close(),
  };
}
