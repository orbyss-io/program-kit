/** Bounded authored locations from the actual runner/source inventory. No raw title, path, error, DOM or stream text. */
import {readFileSync, realpathSync, statSync, unlinkSync, rmdirSync, mkdirSync, writeFileSync} from 'node:fs';
import {resolve, relative, dirname, isAbsolute} from 'node:path';

export function suppressPrivateErrors(info) {
  for (const error of info.errors) {
    for (const key of Object.keys(error)) Reflect.deleteProperty(error,key);
    error.value = info.status === 'timedOut' ? 'Private check timed out.' : 'Private check failed.';
  }
}

export default class PrivateDiagnostics {
  constructor(options = {}) {
    this.options = options; this.rows = []; this.locations = new Map(); this.stages = new Map();
    this.ownedAttachmentParents = new Set();
    this.counts = {stdoutEvents:0,stderrEvents:0,stdoutBytes:0,stderrBytes:0,errors:0,attachments:0,unknownLocations:0,externalAttachments:0,omittedCases:0};
  }
  printsToStdio() { return true; }
  onBegin(config,suite) {
    this.outputDirectory = resolve(config.projects[0].outputDir);
    this.output = resolve(this.outputDirectory, this.options.outputFile ?? 'private-results.json');
    const outputRelative = relative(this.outputDirectory,this.output);
    if (outputRelative.startsWith('..') || isAbsolute(outputRelative)) throw new Error('Private report must stay in its owned output directory.');
    const roots = config.projects.map(project => realpathSync(project.testDir));
    const tests = suite.allTests();
    const files = [...new Set(tests.map(test => test.location.file))].sort();
    const inventory = [];
    for (const [index,file] of files.slice(0,64).entries()) {
      try {
        const physical = realpathSync(file);
        const owned = roots.some(root => { const path=relative(root,physical); return !path.startsWith('..') && !isAbsolute(path); });
        const size = statSync(physical).size;
        if (!owned || physical !== resolve(file) || size > 1048576) continue;
        const source = readFileSync(physical);
        const lines = source.toString('utf8').split(/\r?\n/u).length;
        const sourceId = 'source-' + (index+1);
        inventory.push({sourceId,lines});
        for (const [number,test] of tests.filter(test => test.location.file === file).entries()) {
          const line = test.location.line;
          if (Number.isSafeInteger(line) && line > 0 && line <= lines)
            this.locations.set(test.id,{caseId:sourceId+'-case-'+(number+1),sourceId,line});
        }
      } catch { /* Missing/aliased inventory is unknown, never reconstructed from an error stack. */ }
    }
    this.inventory = inventory;
  }
  onStdOut(chunk) { this.counts.stdoutEvents++; this.counts.stdoutBytes += Buffer.byteLength(chunk); }
  onStdErr(chunk) { this.counts.stderrEvents++; this.counts.stderrBytes += Buffer.byteLength(chunk); }
  onError() { this.counts.errors++; this.counts.unknownLocations++; }
  onStepEnd(test,result,step) {
    if (step.error) this.stages.set(test.id, ['expect','hook','fixture','test.step'].includes(step.category) ? step.category : 'unknown');
  }
  onTestEnd(test,result) {
    const location = this.locations.get(test.id) ?? {caseId:'unknown',sourceId:null,line:null};
    if (location.caseId === 'unknown') this.counts.unknownLocations++;
    this.counts.errors += result.errors.length;
    this.counts.attachments += result.attachments.length;
    for (const attachment of result.attachments) {
      if (!attachment.path) continue;
      const path = resolve(attachment.path);
      const within = relative(this.outputDirectory,path);
      try {
        if (within.startsWith('..') || isAbsolute(within) || realpathSync(path) !== path) this.counts.externalAttachments++;
        else {
          unlinkSync(path);
          for (let parent=dirname(path); parent !== this.outputDirectory; parent=dirname(parent)) {
            const location=relative(this.outputDirectory,parent);
            if (location.startsWith('..') || isAbsolute(location)) break;
            this.ownedAttachmentParents.add(parent);
          }
        }
      } catch { this.counts.externalAttachments++; }
    }
    result.attachments = []; result.stdout = []; result.stderr = [];
    suppressPrivateErrors(result);
    if (this.rows.length < 1024) this.rows.push({...location,status:result.status,retry:result.retry,durationMilliseconds:result.duration,
      stage:result.status === 'timedOut' ? 'timeout' : this.stages.get(test.id) ?? (result.status === 'passed' ? 'completed' : 'unknown')});
    else this.counts.omittedCases++;
    this.stages.delete(test.id);
  }
  onEnd(result) {
    // Remove only now-empty parents of actual owned attachments, never recursive trees or authored input.
    for (const path of [...this.ownedAttachmentParents].sort((a,b)=>b.length-a.length)) {
      try { if (realpathSync(path) === path) rmdirSync(path); }
      catch { this.counts.externalAttachments++; }
    }
    const report = {schemaVersion:1,status:result.status,inventory:this.inventory ?? [],outcomes:this.rows,counts:this.counts,
      limits:['Locations come from this local runner and bounded current source inventory; no authenticated author or inferred stack/cause.',
        'Hook category is observed; setup versus teardown requires the authored case/runner context.',
        'No raw stream/error/attachment hashes; other reporters, application logging and external attachments require their own privacy qualification.']};
    if (this.output) { mkdirSync(dirname(this.output),{recursive:true}); writeFileSync(this.output,JSON.stringify(report,null,2)); }
    process.stdout.write(JSON.stringify(report)+'\n');
    if (this.counts.externalAttachments) return {status:'failed'};
  }
}
