import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {readBackend,forAudience} from '../shared/gediv-gateway.mjs';
import {dashboardModel,legacyView} from '../shared/gediv-client.mjs';
import {toCatalogue} from '../shared/catalog-adapter.mjs';
if(process.stdin.isTTY)execFileSync('stty',['-echo'],{stdio:['inherit','ignore','ignore']});
console.log('Ready for read-only backend verification JSON on stdin.');
let buffer='';process.stdin.setEncoding('utf8');
const line=await new Promise(resolve=>process.stdin.on('data',chunk=>{buffer+=chunk;if(buffer.includes('\n'))resolve(buffer.split('\n')[0]);}));
try{
 const source=await readBackend(JSON.parse(line).token);
 const snapshot=await forAudience(source,true),publicData=await forAudience(source,false);
 const model=dashboardModel(snapshot),legacy=legacyView(snapshot),catalogue=toCatalogue(snapshot);
 assert.equal(model.metrics.decisions,legacy.records.length);
 assert.equal(model.metrics.decisions,catalogue.records.filter(r=>r.validation===(model.scope==='pendente'?'pendente':'validado')).length);
 assert.equal(publicData.rows.length,source.dashboard.counts.confirmed);
 console.log(JSON.stringify({live:true,revision:source.dashboard.revision,counts:source.dashboard.counts,
   interactive:model.metrics,legacyRows:legacy.records.length,siteRows:catalogue.records.filter(r=>r.validation==='pendente').length,
   publicRows:publicData.rows.length,persistentWrites:false}));
 process.exit(0);
}catch(error){console.log(JSON.stringify({live:false,error:error.message,cause:error.cause?.code||error.cause?.message||null,persistentWrites:false}));process.exit(1);}
