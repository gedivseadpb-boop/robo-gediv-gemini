import {dashboardModel,validateSnapshot} from './gediv-client.mjs';
const SERVICES={'TS-01':'anotacao','TS-02':'desaverbacao','TS-03':'licenca_particular','TS-04':'desistencia',
  'TS-05':'licenca_especial','TS-06':'conversao_licenca','TS-07':'conversao_ferias'};

// Adapta campos; mantém o estado documental original, sem conferir candidatos.
export function toCatalogue(snapshot, scope=snapshot.dashboard.defaultScope) {
  validateSnapshot(snapshot);
  if (snapshot.meta.access !== 'manager') scope='conferido';
  const model=dashboardModel(snapshot,{validation:scope});
  const sourceRows=snapshot.meta.access==='manager'?snapshot.rows:snapshot.rows.filter(r=>r.validation==='conferido');
  const records=sourceRows.filter(r=>r.validation!=='rejeitado').map(r=>({
    id:r.id,edition:r.date,url:r.url,page:Number(r.page)||0,pageConfirmed:Number(r.page)>0,
    blockId:r.resenha_id,resenha:r.resenha,actType:'resenha',nature:'publicacao',
    axis:r.axis==='tempo'?'tempo':r.modality==='Vertical'?'vertical':r.modality==='Horizontal'?'horizontal':'outros',
    modality:r.axis==='tempo'?SERVICES[r.category]||'':r.modality==='Vertical'?'vertical':r.modality==='Horizontal'?'horizontal':'',
    originalSubject:r.modality||new Map(snapshot.categories).get(r.category)||'',
    result:['deferido','indeferido'].includes(r.merit)?r.merit:null,resultOriginal:r.merit||'',
    validation:r.validation==='conferido'?'validado':'pendente',fieldStates:{validation:r.validation},
    process:r.process,server:r.server,registration:r.registration||'',org:'Secretaria de Estado da Administração',
    quote:r.evidence||'',sourceType:'backend_privado',notes:scope==='pendente'?'Dados preliminares, em conferência.':'Decisão conferida.',
    ruleVersion:'gediv-backend-v1',group:r.group||'Não informado'
  }));
  const editions=[...new Map(sourceRows.filter(r=>r.url).map(r=>[r.url,{
    id:r.url,date:r.date,url:r.url,status:'parcial',attempts:0,
    records:model.rows.filter(x=>x.url===r.url).length
  }])).values()];
  return {version:1,updatedAt:null,preparedOn:new Date().toLocaleDateString('en-CA',{timeZone:'America/Fortaleza'}),
    records,editions,inventoryComplete:false,inventoryFrom:'2026-01-01',inventoryUntil:new Date().toLocaleDateString('en-CA',{timeZone:'America/Fortaleza'}),
    logs:[],discoveryQueue:[],visited:[],rulesVersion:'gediv-backend-v1',
    gediv:{revision:snapshot.dashboard.revision,scope,access:snapshot.meta.access,counts:snapshot.dashboard.counts,
      label:model.label,preliminary:model.preliminary,connected:true,coverage:snapshot.meta.coverage||'Cobertura parcial.'}};
}

export function emptyCatalogue(){
  return {version:1,updatedAt:null,preparedOn:new Date().toISOString().slice(0,10),records:[],editions:[],
    inventoryComplete:false,inventoryFrom:'2026-01-01',inventoryUntil:new Date().toISOString().slice(0,10),
    logs:[],discoveryQueue:[],visited:[],rulesVersion:'gediv-backend-v1',storageUnavailable:true};
}
