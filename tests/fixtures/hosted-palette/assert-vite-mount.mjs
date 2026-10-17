import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { modules } from './presentation-recording.mjs';
// This test exercises the unchanged built Vite modules, retained revision bytes,
// and mount export. Native transport is an explicit recording, never acceptance.
const observed = new Set();
registerHooks({resolve(specifier,context,next) {
  if (Object.hasOwn(modules,specifier)) {
    observed.add(specifier);
    return {url:'data:text/javascript,'+encodeURIComponent(modules[specifier]),shortCircuit:true};
  }
  return next(specifier,context);
}});
function element() {
  const values=new Map();
  return {hidden:false,inert:false,children:[],style:{getPropertyValue:k=>values.get(k)||'',
    getPropertyPriority:()=>'',setProperty:(k,v)=>values.set(k,v),removeProperty:k=>values.delete(k)},
    setAttribute(){},addEventListener(){},remove(){},insertAdjacentElement(){},
    replaceChildren(...children){this.children=children;},append(...children){this.children.push(...children);}};
}
globalThis.location={href:'http://fixture.invalid/',pathname:'/'};
globalThis.window={addEventListener(){},removeEventListener(){}};
globalThis.document={createElement:element,createTextNode:text=>({textContent:text}),
  head:{append(sheet){queueMicrotask(()=>sheet.onload());}}};
const entry=await import(process.argv[2]);
assert.equal(typeof entry.mount,'function');
const root=element();await entry.mount(root);
assert.equal(root.children[0].textContent,process.argv[3]);
assert.equal(root.hidden,false);assert.equal(root.inert,false);
assert(observed.size===0 || observed.size===Object.keys(modules).length,'Incomplete presentation recording');
