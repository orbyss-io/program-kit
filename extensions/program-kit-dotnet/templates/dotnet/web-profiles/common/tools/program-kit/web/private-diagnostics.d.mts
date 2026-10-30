/** The runtime mutates only the runner's public error objects. */
export function suppressPrivateErrors(info: { status?: string | undefined; errors: object[] }): void;
export default class PrivateDiagnostics {
  constructor(options?: { outputFile?: string });
}
