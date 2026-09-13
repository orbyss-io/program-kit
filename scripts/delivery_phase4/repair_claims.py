"""Start explicit verification contributions under the corrected synthetic policy."""
import json
from pathlib import Path
import sys
from execution_setup import ROOT, REPOS
sys.path.insert(0, str(ROOT / 'extensions/program-kit-delivery/scripts'))
from azure_transport import AzureTransport
from azure_provider import AzureProvider
from delivery_contract import authority
from delivery import write
import azure_execution as execution


def main():
    output = ROOT / 'artifacts/delivery-phase4'
    provider = AzureProvider(AzureTransport('Unfussiness'), authority.read(output / 'profile.json'))
    roots = authority.read(output / 'consumers/repositories.json')
    path = output / 'repair-claims.json'
    results = authority.read(path) if path.exists() else {}
    for name, key in (('api', 'P4-API'), ('client', 'P4-CLIENT')):
        if key in results:
            continue
        claim = execution.claim(provider, key, 'phase4-' + name + '-corrected-policy', roots)
        receipt = authority.read(Path(roots[REPOS[name]]) / execution.RECEIPT)
        check = execution.checkpoint(provider, receipt, 'implementation', roots)
        results[key] = {'claim': claim, 'admission': check}
        write(path, results)
        print(json.dumps({'workId': key, 'generation': claim['generation'], 'admission': check['admission']}), flush=True)


if __name__ == '__main__':
    main()
