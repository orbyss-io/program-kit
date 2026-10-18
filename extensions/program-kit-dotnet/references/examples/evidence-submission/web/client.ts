import type { components } from './types';

type EvidenceRequest = components['schemas']['EvidenceRequest'];
type EvidenceResponse = components['schemas']['EvidenceResponse'];
type EvidenceInputContract = components['schemas']['EvidenceInputContract'];

export async function readInputContract(signal: AbortSignal): Promise<EvidenceInputContract> {
  const headers = { 'X-Fixture-Owner': 'fictional-reviewer' };
  const options: RequestInit = { headers, signal, cache: 'no-store' };
  const response = await fetch('/desk/api/evidence-input', options);
  if (!response.ok) throw new Error('Input contract is unavailable.');
  return response.json() as Promise<EvidenceInputContract>;
}

/** Thin transport adapter over actual generated contracts. The caller owns one operation deadline. */
async function request(
  path: string,
  method: 'GET' | 'POST',
  signal: AbortSignal,
  value?: EvidenceRequest
): Promise<EvidenceResponse> {
  const headers = { 'Content-Type': 'application/json', 'X-Fixture-Owner': 'fictional-reviewer' };
  const body = value === undefined ? undefined : JSON.stringify(value);
  const options: RequestInit = { method, headers, signal, cache: 'no-store' };
  if (body !== undefined) options.body = body;
  const response = await fetch(path, options);
  if (!response.ok) throw new Error('Submission could not be observed.');
  return response.json() as Promise<EvidenceResponse>;
}

export function prepareEvidence(value: EvidenceRequest, signal: AbortSignal) {
  const path = '/desk/api/evidence';
  return request(
    path,
    'POST',
    signal,
    value
  );
}

export function acceptEvidence(identity: string, signal: AbortSignal) {
  const path = `/desk/api/evidence/${identity}/accept`;
  return request(
    path,
    'POST',
    signal
  );
}

export function findEvidence(identity: string, signal: AbortSignal) {
  const path = `/desk/api/evidence/${identity}`;
  return request(
    path,
    'GET',
    signal
  );
}
