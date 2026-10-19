/** Finite browser selection example. Own one generation across file/date/navigation/session.
 * The owner supplies read/digest for deterministic races; this is neither a wire contract nor a crypto canceller.
 */
function readFile(file) {
  const reader = new FileReader();
  const promise = new Promise((resolve, reject) => {
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('File could not be read. Select it again.'));
    reader.onabort = () => reject(new DOMException('Selection cancelled.', 'AbortError'));
    reader.readAsArrayBuffer(file);
  });
  return {promise, abort: () => { if (reader.readyState === FileReader.LOADING) reader.abort(); }};
}

async function digestBytes(bytes) {
  const algorithm = 'SHA-256';
  const digest = await crypto.subtle.digest(algorithm, bytes);
  const values = new Uint8Array(digest);
  return [...values].map(value => value.toString(16).padStart(2, '0')).join('');
}

export function createFileSelection({maximumBytes, maximumTitleLength, read = readFile, digest = digestBytes, timeoutMilliseconds = 2000} = {}) {
  if (!Number.isSafeInteger(maximumBytes) || maximumBytes < 1 || maximumBytes > 1048576
      || !Number.isSafeInteger(maximumTitleLength) || maximumTitleLength < 1 || maximumTitleLength > 1024)
    throw new TypeError('Supply the admitted owning input contract.');
  if (!Number.isSafeInteger(timeoutMilliseconds) || timeoutMilliseconds < 1 || timeoutMilliseconds > 30000)
    throw new TypeError('A bounded selection deadline is required.');
  let generation = 0;
  let pending;
  let disposed = false;
  let state = Object.freeze({kind: 'empty', generation});
  function invalidate() {
    generation++;
    pending?.abort(); pending = undefined;
    state = Object.freeze({kind: 'empty', generation});
  }
  async function select(file, date) {
    if (disposed) throw new Error('Selection owner is disposed.');
    invalidate();
    const current = generation;
    state = Object.freeze({kind: 'reading', generation: current});
    let timer;
    try {
      if (!file || file.size < 1 || file.size > maximumBytes || !/^\d{4}-\d{2}-\d{2}$/u.test(date))
        throw new Error('Select a date and a text file within the owning input contract.');
      const active = pending = read(file);
      const deadline = new Promise((_, reject) => {
        timer = setTimeout(() => { active.abort(); reject(new Error('File preparation expired. Select it again.')); }, timeoutMilliseconds);
      });
      const prepare = async () => {
        const buffer = await active.promise;
        const bytes = new Uint8Array(buffer).slice();
        if (bytes.length !== file.size) throw new Error('File changed during preparation.');
        const decoder = new TextDecoder('utf-8', {fatal: true});
        decoder.decode(bytes);
        const hash = await digest(bytes);
        return {bytes, hash};
      };
      const prepared = await Promise.race([prepare(), deadline]);
      if (disposed || current !== generation) return state;
      // Retained bytes are not exposed. A confirmed snapshot is made separately.
      state = Object.freeze({kind: 'ready', generation: current, name: file.name, date, hash: prepared.hash});
      pending = {abort() {}, bytes: prepared.bytes};
    } catch {
      if (!disposed && current === generation) {
        pending = undefined;
        state = Object.freeze({kind: 'failed', generation: current, message: 'File preparation failed. Select the file again.'});
      }
    } finally { clearTimeout(timer); }
    return state;
  }
  return Object.freeze({
    select, invalidate,
    current: () => state,
    confirm(title) {
      if (disposed || state.kind !== 'ready' || !title.length || title.length > maximumTitleLength || /[\u0000-\u001f\u007f-\u009f]/u.test(title))
        throw new Error('Complete the current selection before confirmation.');
      const bytes = pending.bytes.slice();
      const content = btoa(String.fromCharCode(...bytes));
      return Object.freeze({title, date: state.date, content});
    },
    dispose() { invalidate(); disposed = true; },
  });
}
