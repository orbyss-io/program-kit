/** Synthetic native-module recordings for Vite asset/renderer tests; no authentication acceptance. */
export const modules = {
  '/auth/assets/v1/configuration.mjs': `export async function loadBrowserPresentation() {
    return {surface:'/',modulePath:'/auth/assets/v1/presentation.mjs',bffModulePath:'/auth/assets/v1/bff.mjs',
      antiforgeryPath:'/bff/antiforgery',logoutPath:'/bff/logout',signOutConfirmation:'always'}; }`,
  '/auth/assets/v1/presentation.mjs': `export function unsavedWork() { return {register(){return () => {};}}; }`,
  '/auth/assets/v1/bff.mjs': `export async function prepareBffSignOut() { return {request:async()=>{},dispose(){}}; }`,
  '/auth/assets/v1/session.mjs': `export function observeBffSession(options) {
    options.onObservation({state:'authenticated'}); return {ready:Promise.resolve(),dispose(){}}; }`,
};
