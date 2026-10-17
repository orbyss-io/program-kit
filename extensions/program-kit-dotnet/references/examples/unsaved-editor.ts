import type { UnsavedWorkSource, UnsavedWorkState } from './foundation-browser/presentation.mjs';

/** Application-owned state; the shared registry never saves or discards drafts. */
export function attachExampleEditor(root: HTMLElement,
  presentation: { registerUnsavedWork(source: UnsavedWorkSource): () => void }) {
  const editor = document.createElement('textarea'); editor.setAttribute('aria-label', 'Example draft');
  let state: UnsavedWorkState = 'clean';
  const changed = () => { state = 'dirty'; };
  editor.addEventListener('input', changed); root.append(editor);
  const unregister = presentation.registerUnsavedWork({ getState: () => state });
  return {
    beginSave() { state = 'unknown'; },
    acknowledgeSave() { state = 'clean'; },
    markUncertain() { state = 'unknown'; },
    dispose() { unregister(); editor.removeEventListener('input', changed); editor.remove(); },
  };
}
