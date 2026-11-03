import {validateSnapshot, dashboardModel} from './gediv-client.mjs';

// O destino é fixo. Credenciais nunca são enviadas a URLs fornecidas pelo navegador.
export const BACKEND_ORIGIN = 'https://gediv-conferencia-privada-20261031.ylenaluna.chatgpt.site';
export const DATA_HEADERS = {'Cache-Control':'private, no-store', 'Vary':'Cookie, oai-authenticated-user-id',
  'X-Content-Type-Options':'nosniff','Cross-Origin-Resource-Policy':'same-origin'};

export async function readBackend(token, fetcher=fetch) {
  if (!token || typeof token !== 'string') throw Error('Conexão privada ainda não configurada no servidor.');
  const response = await fetcher(BACKEND_ORIGIN+'/api/data', {
    method:'GET', redirect:'error', cache:'no-store', signal:AbortSignal.timeout(15000),
    headers:{Accept:'application/json','OAI-Sites-Authorization':'Bearer '+token}
  });
  if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw Error('Backend privado indisponível: HTTP '+response.status+' ('+(response.headers.get('content-type')||'sem Content-Type')+').');
  const reader=response.body?.getReader();
  if (!reader) throw Error('Resposta privada vazia.');
  const chunks=[];let size=0;
  try {
    while (true) {
      const {value,done}=await reader.read();if(done)break;
      size+=value.byteLength;if(size>8*1024*1024){await reader.cancel();throw Error('Resposta acima do limite.');}
      chunks.push(value);
    }
  } finally {reader.releaseLock();}
  const bytes=new Uint8Array(size);let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  return validateSnapshot(JSON.parse(new TextDecoder().decode(bytes)));
}

export async function forAudience(source, manager=false) {
  validateSnapshot(source);
  if (manager) return {...source, meta:{...source.meta, access:'manager',semBaseCarregada:false}};
  // Não serializar o objeto original: ele contém pendências, rejeições e textos de revisão.
  const rows=source.rows.filter(r=>r.validation==='conferido').map(r=>({
    id:r.id,date:r.date,resenha:r.resenha,resenha_id:r.resenha_id,act:r.act||'',
    process:r.process,server:String(r.server||'').split(/\s+/).filter(Boolean).map(s=>s[0]+'.').join(' '),
    registration:'',axis:r.axis,modality:r.modality||'',category:r.category||'',group:r.group||'',
    merit:r.merit,url:r.url,page:r.page,validation:'conferido',evidence:''
  }));
  const acts=new Set(rows.map(r=>r.act).filter(Boolean));
  const events=source.events.filter(e=>e.validation==='conferido'&&e.act&&acts.has(e.act)).map(e=>({
    id:e.id,date:e.date,act:e.act,type:e.type,url:e.url,page:e.page,validation:'conferido',description:''
  }));
  const projected={rows,events,categories:source.categories,groups:[],urls:{},meta:{
    access:'public',semBaseCarregada:false,coverage:'Somente decisões conferidas. Cobertura histórica parcial.',
    automation:'Atualizar consulta os resultados já recebidos; não executa a coleta de PDFs.',
    connection:{source:'backend_privado',partialCoverage:true,fullPeriodComplete:false}
  }};
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify({rows,events})));
  const revision=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
  const views={};
  for(const validation of ['pendente','conferido']){
    const model=dashboardModel(projected,{validation});
    views[validation]={label:model.label,rowIds:model.rows.map(r=>r.id),metrics:model.metrics,series:model.series};
  }
  projected.dashboard={schemaVersion:1,revision,defaultScope:'conferido',counts:{received:rows.length,
    pending:0,confirmed:rows.length,rejected:0,unlinkedEvents:0},views};
  return validateSnapshot(projected);
}

export async function snapshotResponse({manager=false,token='',fetcher=fetch}={}) {
  try {
    const data=await forAudience(await readBackend(token,fetcher),manager);
    return Response.json(data,{headers:{...DATA_HEADERS,'X-GEDIV-Revision':data.dashboard.revision}});
  } catch {
    return Response.json({error:'Não foi possível consultar o backend privado. A última leitura deve ser mantida.'},
      {status:503,headers:DATA_HEADERS});
  }
}
