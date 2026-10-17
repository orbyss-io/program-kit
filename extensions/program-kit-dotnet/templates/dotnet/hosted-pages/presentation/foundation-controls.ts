import type * as Configuration from './foundation-browser/configuration.mjs';
import type * as Presentation from './foundation-browser/presentation.mjs';
import type * as Bff from './foundation-browser/bff.mjs';
import type * as Session from './foundation-browser/session.mjs';

/** Runtime modules remain served by the selected native Foundation feature. */
async function nativeModule<T>(path: string, member: keyof T): Promise<T> {
  const loaded: unknown = await import(/* @vite-ignore */ path);
  if (typeof loaded !== 'object' || loaded === null || !(member in loaded)
      || typeof (loaded as Record<keyof T, unknown>)[member] !== 'function') {
    throw new Error('The selected native browser module is unavailable.');
  }
  return loaded as T;
}

/** Thin application binding; no protocol, confirmation or session implementation. */
export async function bindFoundationPresentation(root: HTMLElement,
  configurationPath = __CONFIGURATION_PATH__) {
  if (!configurationPath.startsWith('/') || configurationPath.includes('//')
      || /[\\\u0000-\u0020\u007f?#%]/u.test(configurationPath)
      || new URL(configurationPath, location.href).pathname !== configurationPath
      || !configurationPath.endsWith('/configuration')) throw new Error('Select a literal native configuration route.');
  const pagePrefix = configurationPath.slice(0, -'/configuration'.length);
  const original = { hidden: root.hidden, inert: root.inert, display: root.style.getPropertyValue('display'),
    priority: root.style.getPropertyPriority('display') };
  root.hidden = true; root.inert = true; root.style.setProperty('display', 'none', 'important');
  const recovery = document.createElement('p'); recovery.setAttribute('role', 'status'); recovery.hidden = true;
  root.insertAdjacentElement('afterend', recovery);
  const controller = new AbortController();
  const stylesheet = document.createElement('link'); stylesheet.rel = 'stylesheet';
  stylesheet.href = pagePrefix + '/assets/v1/page.css';
  let control: Presentation.SignOutControl<void> | undefined;
  let observer: Session.BffSessionObserver | undefined;
  let button: HTMLButtonElement | undefined;
  let disposed = false;
  let privateCleared = false;
  const sources = new Set<() => void>();
  const recover = (message: string) => {
    privateCleared = true;
    for (const unregister of sources) unregister();
    sources.clear();
    root.hidden = true; root.inert = true; root.style.setProperty('display', 'none', 'important');
    root.replaceChildren();
    const link = document.createElement('a'); link.href = pagePrefix + '/sign-in'; link.textContent = 'Sign in';
    recovery.replaceChildren(document.createTextNode(message + ' '), link); recovery.hidden = false;
  };
  const dispose = () => {
    if (disposed) return;
    disposed = true; controller.abort(); control?.dispose(); observer?.dispose();
    for (const unregister of sources) unregister();
    sources.clear(); button?.remove(); recovery.remove(); stylesheet.remove(); window.removeEventListener('pagehide', leave);
  };
  const leave = (event: PageTransitionEvent) => { if (!event.persisted) dispose(); };
  try {
    const loader = await nativeModule<typeof Configuration>(pagePrefix + '/assets/v1/configuration.mjs', 'loadBrowserPresentation');
    const selected = await loader.loadBrowserPresentation(configurationPath, { signal: controller.signal });
    await new Promise<void>((resolve, reject) => {
      const finish = (error?: Error) => {
        clearTimeout(timer); stylesheet.onload = null; stylesheet.onerror = null;
        controller.signal.removeEventListener('abort', cancelled);
        if (error) reject(error); else resolve();
      };
      const cancelled = () => finish(new Error('Native presentation style loading cancelled.'));
      const timer = setTimeout(() => finish(new Error('Native presentation styles unavailable.')), 5000);
      stylesheet.onload = () => finish(); stylesheet.onerror = () => finish(new Error('Native presentation styles unavailable.'));
      controller.signal.addEventListener('abort', cancelled, { once: true }); document.head.append(stylesheet);
    });
    if (!selected.bffModulePath || !selected.antiforgeryPath || !selected.logoutPath)
      throw new Error('The selected application requires its qualified native BFF transport.');
    const [presentation, bff, session] = await Promise.all([
      nativeModule<typeof Presentation>(selected.modulePath, 'unsavedWork'),
      nativeModule<typeof Bff>(selected.bffModulePath, 'prepareBffSignOut'),
      nativeModule<typeof Session>(pagePrefix + '/assets/v1/session.mjs', 'observeBffSession'),
    ]);
    const registry = presentation.unsavedWork(selected.surface);
    control = await bff.prepareBffSignOut({ surface: selected.surface, mode: selected.signOutConfirmation,
      antiforgeryPath: selected.antiforgeryPath, logoutPath: selected.logoutPath, signal: controller.signal });
    const invokingButton = document.createElement('button'); button = invokingButton;
    invokingButton.type = 'button'; invokingButton.textContent = __SIGN_OUT_TEXT__;
    const status = document.createElement('p'); status.setAttribute('role', 'status');
    invokingButton.addEventListener('click', () => {
      void control?.request({ returnFocus: invokingButton }).catch(() => {
        status.textContent = 'Sign-out could not be completed. Session status has not been confirmed.';
      });
    });
    root.append(button, status);
    // Restore the original visibility immediately before the native boundary
    // synchronously hides it and owns all later fresh-session admission.
    root.hidden = original.hidden; root.inert = original.inert;
    if (original.display) root.style.setProperty('display', original.display, original.priority);
    else root.style.removeProperty('display');
    observer = session.observeBffSession({ privateRoots: [root],
      userPath: (selected.surface === '/' ? '' : selected.surface) + '/bff/user', signal: controller.signal,
      onObservation(observation) {
        if (observation.state === 'authenticated' && !privateCleared) recovery.hidden = true;
        else if (observation.state === 'authenticated') {
          const reload = document.createElement('a'); reload.href = location.pathname; reload.textContent = 'Return to application';
          recovery.replaceChildren(reload); recovery.hidden = false;
        }
        else recover(observation.state === 'anonymous' ? 'Sign in to continue.' : 'Session status could not be confirmed.');
        return undefined;
      } });
    window.addEventListener('pagehide', leave);
    await observer.ready;
    return {
      registerUnsavedWork(source: Presentation.UnsavedWorkSource) {
        if (disposed || privateCleared) throw new Error('The application private surface is no longer active.');
        const unregister = registry.register(source); sources.add(unregister);
        return () => { unregister(); sources.delete(unregister); };
      },
      dispose,
    };
  } catch {
    control?.dispose(); observer?.dispose(); controller.abort(); stylesheet.remove();
    recover('Session controls are unavailable.');
    throw new Error('Native application session controls are unavailable.');
  }
}
