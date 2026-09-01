import { expect, test } from '@playwright/test';

const apiPath = process.env.PROGRAMKIT_ROLE_PROBE_PATH ?? '/api/auth-contract';

test('anonymous API request is a stable 401 problem', async ({ request }) => {
  const response = await request.get(apiPath);
  expect(response.status()).toBe(401);
  expect(response.headers()['content-type']).toContain('application/problem+json');
  expect(await response.json()).toMatchObject({ code: 'authentication_required' });
});

test('unlisted browser origin receives no CORS grant', async ({ request }) => {
  const response = await request.fetch(apiPath, {
    method: 'OPTIONS',
    headers: {
      Origin: 'https://not-allowed.example.test',
      'Access-Control-Request-Method': 'GET',
      'Access-Control-Request-Headers': 'authorization',
    },
  });
  expect(response.headers()['access-control-allow-origin']).toBeUndefined();
});

test('consumer supplies the real PKCE browser journey for an explicitly selected SPA client', async ({ page }) => {
  const loginPath = process.env.PROGRAMKIT_SPA_LOGIN_PATH;
  test.skip(!loginPath, 'Set PROGRAMKIT_SPA_LOGIN_PATH to the client route that starts the standard PKCE login.');
  await page.goto(loginPath!);
  await page.locator('#username').fill('local-user');
  await page.locator('#password').fill('local-user-only');
  await page.locator('#kc-login').click();
  await expect(page).not.toHaveURL(/localhost:8080/);
  const storage = await page.evaluate(() => ({ ...localStorage, ...sessionStorage }));
  expect(JSON.stringify(storage)).not.toMatch(/access_token|refresh_token/i);
});
