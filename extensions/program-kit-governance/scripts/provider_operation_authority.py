"""Human-owned one-use provider authority, separate from coding-worker manifests.

Native compatibility evidence is prerequisite evidence, not consent to spend.
Only the separate interactive terminal issuer creates provider-mode attestations.
Recording-mode issuance is explicitly fictional and cannot authorize provider I/O.
Local files are attestations, not cryptographic proof of a person's identity.
"""
from __future__ import annotations
import argparse
import getpass
import math
from pathlib import Path
import sys
import time
import uuid


def scope(prepared, native):
    from provider_operation import ADAPTER
    value = prepared['value']
    return {'contractPath':prepared['path'],'contractSha256':prepared['sha256'],
            'fixtureSha256':prepared['fixtureSha256'],'account':value['account'],
            'operation':value['operation'],'adapter':ADAPTER,'resourceIdentity':prepared['resource'],
            'limits':value['limits'],'submitBefore':value['submitBefore'],'recoverBefore':value['recoverBefore'],
            'nativeAdmission':native}


def read(root, path, prepared, native, execution, *, recovery=False):
    from provider_operation import require, load, local, canonical, sha
    require(execution in ('recording','provider'), 'select an explicit qualified execution mode')
    target = local(root,path)
    value = load(target)
    require(isinstance(value,dict) and set(value)=={'schemaVersion','kind','id','execution','issuer','issuedAt','expiresAt','scope'},
            'unsupported one-use provider authorization')
    require(type(value['schemaVersion']) is int and value['schemaVersion']==1 and value['kind']=='provider-operation-one-use'
            and str(uuid.UUID(value['id']))==value['id'] and value['execution']==execution,
            'provider authority cannot be borrowed from another phase or recording mode')
    require(value['scope']==scope(prepared,native), 'one-use provider authority has different exact inputs or limits')
    issuer = value['issuer']
    require(isinstance(issuer,dict) and set(issuer)=={'kind','name','confirmationSha256'}
            and issuer['kind']==('fictional-recording' if execution=='recording' else 'human-terminal')
            and isinstance(issuer['name'],str) and 0<len(issuer['name'])<=256,
            'provider execution needs its separate attributable human terminal attestation')
    expected = confirmation(prepared)
    require(issuer['confirmationSha256']==sha(expected.encode()), 'one-use provider confirmation scope changed')
    require(type(value['issuedAt']) in (int,float) and type(value['expiresAt']) in (int,float)
            and math.isfinite(value['issuedAt']) and math.isfinite(value['expiresAt'])
            and value['issuedAt']<=value['expiresAt']<=min(value['scope']['submitBefore'],value['issuedAt']+300),
            'one-use provider issuance exceeds its bounded confirmation lifetime')
    if not recovery:
        require(value['issuedAt']<=time.time()<value['expiresAt'], 'one-use provider authority expired')
    return {'path':path,'sha256':sha(target.read_bytes()),'kind':'provider-operation-one-use',
            'execution':execution,'nativeAdmission':native}


def confirmation(prepared):
    value = prepared['value']
    return ('AUTHORIZE ONE OCR READ '+prepared['sha256']+' RESERVE '+str(value['limits']['runReservationMicroUsd'])
            +' MICROUSD TOTAL CEILING '+str(value['limits']['aggregateCeilingMicroUsd'])+' MICROUSD')


def issue_recording(root, path, prepared, native):
    """Test/rehearsal input only. Its execution discriminator always remains recording."""
    return _write(root,path,prepared,native,'recording','fictional-recording','synthetic fixture')


def _write(root, path, prepared, native, execution, issuer_kind, name):
    from provider_operation import canonical, sha, local, require
    now = time.time()
    require(execution=='recording' or execution=='provider' and sys.stdin.isatty() and sys.stdout.isatty(),
            'provider attestation issuance is human terminal owned; recording authority never enables provider transport')
    require(now<prepared['value']['submitBefore'], 'cannot issue expired operation authority')
    value = {'schemaVersion':1,'kind':'provider-operation-one-use','id':str(uuid.uuid4()),'execution':execution,
             'issuer':{'kind':issuer_kind,'name':name,'confirmationSha256':sha(confirmation(prepared).encode())},
             'issuedAt':now,'expiresAt':min(now+300,prepared['value']['submitBefore']),'scope':scope(prepared,native)}
    target = local(root,path)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:
        stream.write(canonical(value));stream.flush()
        import os
        os.fsync(stream.fileno())
    return path


def main():
    parser = argparse.ArgumentParser(description='Human terminal only: issue one exact OCR-only provider operation attestation. Never run this issuer from an agent, CI or hook.')
    parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--contract',required=True)
    parser.add_argument('--prerequisite',required=True)
    parser.add_argument('--recipe',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    from provider_operation import contract, native_admission, require, Account
    require(sys.stdin.isatty() and sys.stdout.isatty(), 'provider authority issuer requires the human-owned interactive terminal; no approved/yes flag exists')
    root = args.repository.resolve()
    prepared = contract(root,args.contract)
    from provider_operation_prepare import verify
    adapter=prepared['value']['adapterPreparation']
    verify(root,adapter['path'],adapter['sha256'])
    native = native_admission(root,prepared,args.prerequisite,args.recipe)
    account=Account(root,prepared['resource']).review()
    import json
    print(json.dumps(account,indent=2))
    require(account['aggregateReservedMicroUsd']+prepared['value']['limits']['runReservationMicroUsd']<=
            min(account['originalCeilingMicroUsd'],prepared['value']['limits']['aggregateCeilingMicroUsd']),
            'retained reservations leave no capacity for this operation')
    print('Exact one-page OCR only; zero model calls/retry/fallback. Existing reservations and unknown outcomes remain charged.')
    print('Resource: '+prepared['resource'])
    print('Review the original historical mappings and all uncertain outcomes above; they remain charged.')
    print('Recover only within the exact declared polling/deletion limits; this grants no paid coding-worker authority.')
    expected = confirmation(prepared)
    print(expected)
    require(input('Type the complete line to authorize: ')==expected, 'exact human confirmation was not supplied; no authority issued')
    path = _write(root,args.output,prepared,native,'provider','human-terminal',getpass.getuser())
    print('One-use provider authority: '+path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
