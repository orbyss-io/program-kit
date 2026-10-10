// Application assertions only. Maintained tooling supplies services and sessions.
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
function privateResponsePolicy(response) {
  const headers = response.headers();
  assert.ok(headers['cache-control'].includes('no-store'));
  assert.ok(headers['x-robots-tag'].includes('noindex'));
  const followingSupported = process.env.PROGRAMKIT_CRAWLER_FOLLOWING_QUALIFIED === 'true';
  if (followingSupported) assert.ok(headers['x-robots-tag'].includes('nofollow'));
  return {cacheControl:headers['cache-control'], robotsTag:headers['x-robots-tag'], followingSupported};
}
export async function qualify({user, admin, wrongRole}) {
  if (process.env.PROGRAMKIT_RETAINED_RESOURCE_ID) {
    const id=process.env.PROGRAMKIT_RETAINED_RESOURCE_ID;
    const retained=await user.request.get(`/resources/${id}`);
    assert.equal(retained.status(),200);
    assert.equal((await retained.json()).id,id);
    const responsePolicy=privateResponsePolicy(retained);
    assert.equal((await admin.request.get(`/resources/${id}`)).status(),404);
    return {status:'passed',ownedCreateRead:true,retainedAfterRestart:true,ownerIsolation:true,resourceId:id,responsePolicy};
  }
  const id = randomUUID();
  const token = await (await user.request.get('/bff/antiforgery')).json();
  const headers = {[token.headerName]:token.requestToken};
  const created = await user.request.put(`/resources/${id}`, {headers});
  assert.equal(created.status(),201);
  const found = await user.request.get(`/resources/${id}`);
  assert.equal(found.status(),200);
  assert.equal((await found.json()).id,id);
  const responsePolicy=privateResponsePolicy(found);
  assert.equal((await admin.request.get(`/resources/${id}`)).status(),404);
  assert.equal((await wrongRole.request.get(`/resources/${id}`)).status(),404);
  assert.equal((await user.request.put(`/resources/${id}`,{headers})).status(),409);
  assert.equal((await user.request.get(`/resources/${id}`)).status(),200);
  return {status:'passed',ownedCreateRead:true,ownerIsolation:true,conflictPreservesResource:true,resourceId:id,responsePolicy,
          semantics:'Application owns issuer/subject resource predicate and conflict mapping; no full Notes replay/retention claim.'};
}
