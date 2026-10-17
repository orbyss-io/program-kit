import { expect, test } from '@playwright/test';
import {
  createProgramKitLogoutChannel,
  evaluateProgramKitSession,
  localFirstProgramKitLogout,
  type ProgramKitSessionPolicy,
} from '../spa-session.js';

const policy: ProgramKitSessionPolicy = {
  idleMinutes: 30,
  absoluteMinutes: 480,
  absoluteDeadlineClaim: 'auth_time',
  tokenExpiryClaim: 'exp',
  crossTabCoordination: 'required-no-token-payload',
  providerLogoutFailure: 'local-session-remains-cleared',
};

test('silent renewal cannot move the original absolute deadline', () => {
  const decision = evaluateProgramKitSession(policy, {
    nowSeconds: 28_801,
    authTimeSeconds: 0,
    tokenExpiresAtSeconds: 40_000,
    lastActivityAtSeconds: 28_000,
  });
  expect(decision).toEqual({ active: false, reason: 'absolute-expiry' });
});

test('idle and token expiry both terminate the local session', () => {
  expect(evaluateProgramKitSession(policy, {
    nowSeconds: 2_000,
    authTimeSeconds: 0,
    tokenExpiresAtSeconds: 3_000,
    lastActivityAtSeconds: 100,
  })).toEqual({ active: false, reason: 'idle-expiry' });
  expect(evaluateProgramKitSession(policy, {
    nowSeconds: 1_000,
    authTimeSeconds: 0,
    tokenExpiresAtSeconds: 999,
    lastActivityAtSeconds: 900,
  })).toEqual({ active: false, reason: 'token-expiry' });
});

test('provider failure cannot restore locally cleared authentication', async () => {
  let authenticated = true;
  const result = await localFirstProgramKitLogout(
    () => { authenticated = false; },
    () => { throw new Error('provider unavailable'); },
  );
  expect(result).toBe('provider-unavailable');
  expect(authenticated).toBeFalsy();
});

test('native provider dispatch stays in the original gesture stack after synchronous clearing', async () => {
  let eventStack = true;
  let local = true;
  const logout = localFirstProgramKitLogout(() => { local = false; }, () => {
    expect(eventStack).toBeTruthy();
    expect(local).toBeFalsy();
  });
  eventStack = false;
  expect(await logout).toBe('provider-started');
});

test('asynchronous local clearing cannot dispatch a provider operation', async () => {
  let dispatched = 0;
  await expect(localFirstProgramKitLogout(async () => undefined, () => { dispatched += 1; }))
    .rejects.toThrow('PKW107');
  expect(dispatched).toBe(0);
});

test('actual browser popup observes the original trusted gesture and cleared local state', async ({ page }) => {
  await page.setContent('<button type="button">Sign out</button>');
  await page.evaluate((source) => {
    const logout = new Function('return (' + source + ')')() as typeof localFirstProgramKitLogout;
    let authenticated = true;
    document.querySelector('button')!.addEventListener('click', () => {
      void logout(() => { authenticated = false; }, () => {
        Object.assign(window, { logoutObservation: { activation: navigator.userActivation.isActive, authenticated } });
        const popup = window.open('about:blank', 'program-kit-owned-gesture-probe');
        if (!popup) throw new Error('owned browser refused popup');
      });
    });
  }, localFirstProgramKitLogout.toString());
  const popup = page.waitForEvent('popup');
  await page.getByRole('button', { name: 'Sign out' }).click();
  const opened = await popup;
  expect(await page.evaluate(() => (window as unknown as { logoutObservation: unknown }).logoutObservation))
    .toEqual({ activation: true, authenticated: false });
  await opened.close();
});

test('cross-tab coordination sends only the fixed signed-out event', async () => {
  let resolveReceived: (() => void) | undefined;
  const received = new Promise<void>((resolve) => { resolveReceived = resolve; });
  const name = `program-kit-test-${Date.now()}`;
  const sender = createProgramKitLogoutChannel(() => undefined, name);
  const receiver = createProgramKitLogoutChannel(() => resolveReceived?.(), name);
  try {
    sender.announceSignOut();
    await received;
  } finally {
    sender.close();
    receiver.close();
  }
});
