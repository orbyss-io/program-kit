import type { paths } from '../../../tools/openapi/policies/generated/types';

export type LabelRequest = paths['/api/sample-label']['post']['requestBody']['content']['application/json'];
export type LabelResponse = paths['/api/sample-label']['post']['responses'][200]['content']['application/json'];

// Application-owned transport adapter checked against the maintained generated
// paths. It neither generates a substitute schema nor retries an uncertain write.
export async function storeLabel(
  value: LabelRequest,
  headerName: string,
  requestToken: string,
  signal: AbortSignal
): Promise<LabelResponse> {
  signal.throwIfAborted();
  if (headerName !== 'X-CSRF-TOKEN' || typeof requestToken !== 'string' || !requestToken) {
    throw new Error('The sample requires an admitted native BFF antiforgery token.');
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)
      || typeof value.policy !== 'string' || Object.keys(value).some(key => key !== 'policy')) {
    throw new Error('The sample request differs from its strict wire contract.');
  }
  const serialized = JSON.stringify(value);
  // Exact selected sample-label-request profile, not a second business-length policy.
  if (new TextEncoder().encode(serialized).byteLength > 1024) {
    throw new Error('The sample request exceeds its declared transport budget.');
  }
  const options: RequestInit = {
    method: 'POST', credentials: 'same-origin', cache: 'no-store', redirect: 'error', signal,
    headers: { 'content-type': 'application/json', [headerName]: requestToken },
    body: serialized,
  };
  const response = await fetch('/api/sample-label', options);
  if (!response.ok) throw new Error('The sample write needs explicit outcome handling.');
  const body: unknown = await readResponse(response, signal);
  if (!body || typeof body !== 'object' || !('policy' in body) || typeof body.policy !== 'string') {
    throw new Error('The sample response differs from its declared wire contract.');
  }
  return { policy: body.policy };
}

/** Bounds actual bytes using the selected sample-label-response profile; no stage restarts the caller's deadline. */
async function readResponse(response: Response, signal: AbortSignal): Promise<unknown> {
  if (response.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json' || !response.body) {
    throw new Error('The sample response requires the declared JSON representation.');
  }
  const reader = response.body.getReader();
  const bytes = new Uint8Array(2048);
  let count = 0;
  try {
    while (true) {
      signal.throwIfAborted();
      const part = await reader.read();
      signal.throwIfAborted();
      if (part.done) break;
      if (part.value.byteLength > bytes.byteLength - count) {
        throw new Error('The sample response exceeds its declared transport budget.');
      }
      bytes.set(part.value, count);
      count += part.value.byteLength;
    }
  } finally {
    try { await reader.cancel(); }
    finally { reader.releaseLock(); }
  }
  const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes.subarray(0, count));
  return JSON.parse(text) as unknown;
}
