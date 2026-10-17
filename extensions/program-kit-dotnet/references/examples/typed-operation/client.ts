import type { paths } from '../../../tools/openapi/policies/generated/types';

export type LabelRequest = paths['/api/sample-label']['post']['requestBody']['content']['application/json'];
export type LabelResponse = paths['/api/sample-label']['post']['responses'][200]['content']['application/json'];

// Application-owned transport adapter checked against the maintained generated
// paths. It neither generates a substitute schema nor retries an uncertain write.
export async function storeLabel(value: LabelRequest, headerName: string, requestToken: string, signal: AbortSignal): Promise<LabelResponse> {
  const response = await fetch('/api/sample-label', {
    method: 'POST', credentials: 'same-origin', signal,
    headers: { 'content-type': 'application/json', [headerName]: requestToken },
    body: JSON.stringify(value),
  });
  if (!response.ok) throw new Error('The sample write needs explicit outcome handling.');
  const body: unknown = await response.json();
  if (!body || typeof body !== 'object' || !('policy' in body) || typeof body.policy !== 'string') {
    throw new Error('The sample response differs from its declared wire contract.');
  }
  return { policy: body.policy };
}
