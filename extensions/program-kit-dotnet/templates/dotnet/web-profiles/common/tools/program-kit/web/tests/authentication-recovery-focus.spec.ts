import { expect, test } from '@playwright/test';
import { focusAuthenticationRecovery } from '../authentication-recovery-focus.js';

function fixture(active = true, visible = true) {
  let focused = active; let attempts = 0; let admitFocus = true;
  let afterFocus = () => {}; let hidden = false; let inert = false;
  const frames = new Map<number, () => void>(); let frameId = 0;
  const view = Object.assign(new EventTarget(), {
    requestAnimationFrame: (callback: () => void) => { frames.set(++frameId, callback); return frameId; },
    cancelAnimationFrame: (id: number) => { frames.delete(id); },
  }); const body = {};
  const document = Object.assign(new EventTarget(), {
    defaultView: view, activeElement: body, body, documentElement: {},
    visibilityState: visible ? 'visible' : 'hidden', hasFocus: () => focused,
  });
  const heading = { ownerDocument: document, isConnected: true,
    closest: () => hidden || inert ? {} : null,
    focus: () => { attempts++; if (admitFocus) document.activeElement = heading; afterFocus(); } };
  return { view, document, heading, attempts: () => attempts,
    pendingFrames: () => frames.size,
    flush: () => { const callbacks = [...frames.values()]; frames.clear(); for (const callback of callbacks) callback(); },
    active: (value: boolean) => { focused = value; }, admit: (value: boolean) => { admitFocus = value; },
    hidden: (value: boolean) => { hidden = value; }, inert: (value: boolean) => { inert = value; },
    afterFocus: (action: () => void) => { afterFocus = action; },
    bind: () => focusAuthenticationRecovery(heading as unknown as HTMLElement) };
}

test('waits for the first rendering boundary and removes later activation work', () => {
  const owner = fixture(); owner.bind();
  expect(owner.document.activeElement).toBe(owner.document.body);
  expect(owner.attempts()).toBe(0); expect(owner.pendingFrames()).toBe(1);
  owner.flush();
  expect(owner.document.activeElement).toBe(owner.heading);
  owner.document.activeElement = owner.document.body;
  owner.view.dispatchEvent(new Event('focus')); owner.document.dispatchEvent(new Event('visibilitychange')); owner.flush();
  expect(owner.attempts()).toBe(1);
});

test('defers background recovery until the owner document becomes active', () => {
  const owner = fixture(false); owner.bind(); owner.flush(); expect(owner.attempts()).toBe(0);
  owner.active(true); owner.view.dispatchEvent(new Event('focus')); owner.flush();
  expect(owner.document.activeElement).toBe(owner.heading);
});

test('waits for actual visibility and retries a previously refused focus attempt', () => {
  const owner = fixture(true, false); owner.bind();
  owner.view.dispatchEvent(new Event('focus')); owner.flush(); expect(owner.attempts()).toBe(0);
  owner.document.visibilityState = 'visible'; owner.admit(false);
  owner.document.dispatchEvent(new Event('visibilitychange')); owner.flush(); expect(owner.attempts()).toBe(2);
  owner.admit(true); owner.view.dispatchEvent(new Event('focus')); owner.flush();
  expect(owner.document.activeElement).toBe(owner.heading);
});

test('uses one immediate native fallback when the first eligible focus call is refused', () => {
  const owner = fixture(); owner.admit(false);
  owner.afterFocus(() => owner.admit(true)); owner.bind(); owner.flush();
  expect(owner.attempts()).toBe(2); expect(owner.document.activeElement).toBe(owner.heading);
  expect(owner.pendingFrames()).toBe(0);
  owner.document.activeElement = owner.document.body; owner.view.dispatchEvent(new Event('focus')); owner.flush();
  expect(owner.attempts()).toBe(2);
});

test('refused focus does not retry after user choice, disposal or loss of target eligibility', () => {
  for (const change of ['user-control', 'disconnected', 'inactive', 'hidden', 'inert', 'disposed']) {
    const owner = fixture(); owner.admit(false); const dispose = owner.bind();
    owner.afterFocus(() => {
      if (change === 'user-control') { owner.document.activeElement = {}; owner.document.dispatchEvent(new Event('focusin')); }
      else if (change === 'disconnected') owner.heading.isConnected = false;
      else if (change === 'inactive') owner.active(false);
      else if (change === 'hidden') owner.hidden(true);
      else if (change === 'inert') owner.inert(true);
      else dispose();
    });
    owner.flush(); expect(owner.attempts()).toBe(1);
  }
});

test('preserves user-selected controls before activation and cancels the pending binding', () => {
  const owner = fixture(false); owner.bind();
  owner.view.dispatchEvent(new Event('focus')); expect(owner.pendingFrames()).toBe(1);
  const control = {}; owner.document.activeElement = control; owner.document.dispatchEvent(new Event('focusin'));
  expect(owner.pendingFrames()).toBe(0);
  owner.active(true); owner.view.dispatchEvent(new Event('focus')); owner.flush();
  expect(owner.document.activeElement).toBe(control); expect(owner.attempts()).toBe(0);
  owner.document.activeElement = owner.document.body; owner.view.dispatchEvent(new Event('focus')); owner.flush();
  expect(owner.attempts()).toBe(0);
});

test('replacement disposal and page departure remove pending activation listeners', () => {
  for (const departure of ['dispose', 'pagehide', 'disconnected']) {
    const owner = fixture(false); const dispose = owner.bind();
    owner.view.dispatchEvent(new Event('focus')); expect(owner.pendingFrames()).toBe(1);
    if (departure === 'dispose') dispose();
    else if (departure === 'pagehide') owner.view.dispatchEvent(new Event('pagehide'));
    else owner.heading.isConnected = false;
    if (departure !== 'disconnected') expect(owner.pendingFrames()).toBe(0);
    owner.active(true); owner.view.dispatchEvent(new Event('focus'));
    owner.document.dispatchEvent(new Event('visibilitychange')); owner.flush(); expect(owner.attempts()).toBe(0);
  }
});
