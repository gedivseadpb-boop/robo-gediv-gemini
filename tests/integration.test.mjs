import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {dashboardModel,validateSnapshot,fetchSnapshot,legacyView} from '../shared/gediv-client.mjs';
import {readBackend,forAudience,snapshotResponse,BACKEND_ORIGIN} from '../shared/gediv-gateway.mjs';
import {toCatalogue} from '../shared/catalog-adapter.mjs';

// Dados sintéticos, somente para testes. Nenhum registro é importado no produto.
function fixture(){
 const rows=[['p1','pendente','Vertical','a'],['p2','pendente','Horizontal','b'],['p3','conferido','Vertical','c'],['p4','rejeitado','Horizontal','d']].map(([id,validation,modality,resenha_id])=>({
  id,validation,modality,resenha_id,resenha:'1/2026',process:id,server:'Pessoa de Teste',registration:'987654',
  date:'2026-09-01',axis:'progressao',group:'',category:'',act:id,merit:'deferido',
  url:'https://auniao.pb.gov.br/servicos/doe/2026/setembro/teste.pdf',page:1,evidence:validation==='conferido'?'Texto público':'TEXTO PRIVADO'
 }));
 const value={rows,events:[{id:'e1',validation:'pendente',act:'',type:'Republicação',description:'SEGREDO'}],categories:[],meta:{connection:{partialCoverage:true},coverage:'Base parcial',personal:'REVISÃO PRIVADA'}};
 const views={};for(const validation of ['pendente','conferido']){const model=dashboardModel(value,{validation});views[validation]={rowIds:model.rows.map(r=>r.id),metrics:model.metrics,series:model.series};}
 value.dashboard={schemaVersion:1,revision:'a'.repeat(64),defaultScope:'pendente',counts:{received:4,pending:2,confirmed:1,rejected:1,unlinkedEvents:1},views};return value;
}
test('duas interfaces usam a mesma população sem promover candidatos',async()=>{
 const value=await forAudience(fixture(),true);
 const model=dashboardModel(value),legacy=legacyView(value),catalogue=toCatalogue(value);
 assert.equal(model.metrics.decisions,2);assert.equal(legacy.records.length,2);
 assert.equal(catalogue.records.filter(r=>r.validation==='pendente').length,2);
 assert.equal(catalogue.gediv.revision,value.dashboard.revision);
 assert.equal(model.metrics.resenhas,2);assert.equal(model.metrics.refeitos,null);
 assert.equal(catalogue.records.filter(r=>r.validation==='validado').length,1);
 assert.equal(catalogue.records.find(r=>r.id==='p1').group,'Não informado');
});
test('público não recebe pendentes, rejeitados, matrículas ou textos privados',async()=>{
 const value=await forAudience(fixture(),false);const text=JSON.stringify(value);
 assert.equal(value.rows.length,1);assert.equal(value.rows[0].server,'P. d. T.');
 assert.equal(value.dashboard.defaultScope,'conferido');assert.equal(value.dashboard.counts.pending,0);
 for(const secret of ['p1','p2','p4','987654','TEXTO PRIVADO','REVISÃO PRIVADA','SEGREDO'])assert(!text.includes(secret),secret);
 assert.equal(value.events.length,0);assert.equal(toCatalogue(value,'pendente').gediv.scope,'conferido');
});
test('base sem conferidos continua válida e vazia apenas na consulta pública',async()=>{
 const base=fixture();base.rows[2].validation='pendente';base.dashboard.counts.pending=3;base.dashboard.counts.confirmed=0;
 for(const validation of ['pendente','conferido']){const m=dashboardModel(base,{validation});base.dashboard.views[validation]={rowIds:m.rows.map(r=>r.id),metrics:m.metrics,series:m.series};}
 const value=await forAudience(base,false);assert.equal(value.rows.length,0);validateSnapshot(value);
 assert.equal((await forAudience(base,true)).dashboard.counts.pending,3);
});
test('respostas com contagens ou séries divergentes são recusadas',()=>{
 for(const modify of [v=>v.dashboard.counts.pending=1,v=>v.dashboard.views.pendente.metrics.deferidos=99,
  v=>v.dashboard.views.pendente.series.vertical=0,v=>v.rows[0].url='https://example.test/evil',v=>v.rows[0].id='p2']){
  const value=fixture();modify(value);assert.throws(()=>validateSnapshot(value));
 }
});
test('GET de atualização não apaga a leitura anterior após erro ou resposta inválida',async()=>{
 let current=fixture();const original=current;
 for(const reply of [new Response('Login',{headers:{'Content-Type':'text/html'}}),Response.json({error:'Falha'},{status:503}),Response.json({rows:[]})]){
  await assert.rejects(async()=>{current=await fetchSnapshot({fetcher:async()=>reply});});assert.equal(current,original);
 }
});
test('leitura usa somente a mesma origem e sinal de cancelamento',async()=>{
 const c=new AbortController();let call;
 await fetchSnapshot({signal:c.signal,fetcher:async(...args)=>{call=args;return Response.json(fixture());}});
 assert.equal(call[0],'/api/gediv/data');assert.equal(call[1].method,'GET');assert.equal(call[1].credentials,'same-origin');
 assert.equal(call[1].cache,'no-store');assert.equal(call[1].signal,c.signal);
});
test('credencial fica no servidor e segue exclusivamente para o backend fixo',async()=>{
 let call;await readBackend('credencial-sintetica',async(...args)=>{call=args;return Response.json(fixture());});
 assert.equal(call[0],BACKEND_ORIGIN+'/api/data');assert.equal(call[1].redirect,'error');
 assert.equal(call[1].headers['OAI-Sites-Authorization'],'Bearer credencial-sintetica');
});
test('falha e ausência de configuração retornam 503 sem detalhes privados',async()=>{
 let calls=0;const response=await snapshotResponse({fetcher:async()=>{calls++;throw Error('segredo');}});
 assert.equal(response.status,503);assert.equal(calls,0);assert(!(await response.text()).includes('segredo'));
 assert.equal(response.headers.get('cache-control'),'private, no-store');assert(!response.headers.has('Access-Control-Allow-Origin'));
});
test('template do coletor e entrada de atualização não dependem de dados incorporados',async()=>{
 const interactive=await readFile(new URL('../painel-interativo/app.js',import.meta.url),'utf8');
 const legacy=await readFile(new URL('../site/index.html',import.meta.url),'utf8');
 assert(interactive.includes('fetchSnapshot'));assert(interactive.includes('dashboardModel(data'));
 assert(legacy.includes('__GEDIV_EMBED_DATA__'));assert(legacy.includes('fetchSnapshot'));assert(!legacy.includes('updateAnchor.href=actionLink'));
});
