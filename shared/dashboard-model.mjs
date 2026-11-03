// Uma única regra de projeção para o backend e para os filtros do dashboard.
// Função autocontida: o mesmo código é entregue na página, sem outra leitura de rede.
export function dashboardModel(data,filters={}){
 const scope=filters.validation||data.dashboard?.defaultScope||'pendente';
 if(!['pendente','conferido'].includes(scope))throw new Error('Situação de conferência inválida.');
 const norm=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const dateOK=day=>(!filters.from||day>=filters.from)&&(!filters.to||day<=filters.to);
 const count=(rows,key)=>new Set(rows.map(row=>row[key]).filter(Boolean)).size;
 const categories=new Map(data.categories||[]);
 const matches=row=>{
  if(filters.view==='outras'&&row.axis!=='outros')return false;
  if(filters.axis&&row.axis!==filters.axis)return false;
  if(filters.modality&&(row.axis!=='progressao'||row.modality!==filters.modality))return false;
  if(filters.group&&(row.axis!=='progressao'||(filters.group==='NAO_INFORMADO'?Boolean(row.group):row.group!==filters.group)))return false;
  if(filters.category?.length&&(row.axis!=='tempo'||!filters.category.includes(row.category)))return false;
  if(filters.merit&&row.merit!==filters.merit)return false;
  if(filters.query&&!norm([row.resenha,row.process,row.server,row.registration,row.group,filters.groupNames?.[row.group],row.modality,categories.get(row.category)].join(' ')).includes(norm(filters.query)))return false;
  return true;
 };
 const dim=data.rows.filter(row=>row.validation===scope&&matches(row));
 const original=dim.filter(row=>dateOK(row.date));
 const acts=new Set(dim.map(row=>row.act).filter(Boolean));
 const linked=scope==='conferido'?data.events.filter(event=>event.validation==='conferido'&&event.act&&acts.has(event.act)&&dateOK(event.date)):[];
 const redo=linked.filter(event=>['Retificação','Correção','Republicação'].includes(event.type));
 const voided=linked.filter(event=>event.type==='Tornado sem efeito');
 const metrics={processes:count(original,'process'),resenhas:count(original,'resenha_id'),decisions:original.length,
  deferidos:original.filter(row=>row.merit==='deferido').length,indeferidos:original.filter(row=>row.merit==='indeferido').length,
  refeitos:scope==='conferido'?new Set(redo.map(event=>event.act)).size:null,
  semEfeito:scope==='conferido'?new Set(voided.map(event=>event.act)).size:null};
 let rows=original;
 if(filters.card==='deferidos'||filters.card==='indeferidos')rows=original.filter(row=>row.merit===(filters.card==='deferidos'?'deferido':'indeferido'));
 else if(filters.card==='processes')rows=original.filter(row=>Boolean(row.process));
 else if(filters.card==='refeitos'||filters.card==='semEfeito'){
  const selected=new Set((filters.card==='refeitos'?redo:voided).map(event=>event.act));rows=dim.filter(row=>row.act&&selected.has(row.act));
 }
 const series={vertical:rows.filter(row=>row.axis==='progressao'&&row.modality==='Vertical').length,
  horizontal:rows.filter(row=>row.axis==='progressao'&&row.modality==='Horizontal').length,
  tempo:rows.filter(row=>row.axis==='tempo').length,
  other:rows.filter(row=>!['tempo','progressao'].includes(row.axis)||row.axis==='progressao'&&!['Vertical','Horizontal'].includes(row.modality)).length};
 const timeline=[...new Set(rows.map(row=>row.date))].sort().map(date=>({date,records:rows.filter(row=>row.date===date).length}));
 const groupSeries=[...new Set(rows.filter(row=>row.axis==='progressao').map(row=>row.group||'NAO_INFORMADO'))]
  .map(group=>({group,records:rows.filter(row=>row.axis==='progressao'&&(row.group||'NAO_INFORMADO')===group).length}));
 return {scope,preliminary:scope==='pendente',label:scope==='pendente'?'Em conferência · dados preliminares':'Decisões conferidas',
  rows,original,metrics,redo,voided,series,timeline,groupSeries};
}

// Valida a resposta completa antes de substituir a base já visível no navegador.
export function acceptDashboardSnapshot(next){
 const dashboard=next?.dashboard;
 if(!Array.isArray(next?.rows)||!Array.isArray(next?.events)||!Array.isArray(next?.categories)||!next?.meta?.connection||
  dashboard?.schemaVersion!==1||!/^[0-9a-f]{64}$/.test(dashboard.revision)||!['pendente','conferido'].includes(dashboard.defaultScope))
  throw new Error('Resposta do backend incompatível; a base anterior foi mantida.');
 const counts=dashboard.counts;
 if(!counts||counts.received!==next.rows.length||counts.pending+counts.confirmed+counts.rejected!==counts.received)
  throw new Error('Contagem do backend inconsistente; a base anterior foi mantida.');
 for(const scope of ['pendente','conferido']){
  const rows=next.rows.filter(row=>row.validation===scope),view=dashboard.views?.[scope];
  const ids=new Set(rows.map(row=>row.id));
  if(!view||!Array.isArray(view.rowIds)||view.rowIds.length!==rows.length||new Set(view.rowIds).size!==rows.length||
   view.rowIds.some(id=>!ids.has(id))||view.metrics?.decisions!==rows.length||
   !view.series||Object.values(view.series).reduce((total,n)=>total+n,0)!==rows.length)
   throw new Error('Registros e gráficos do backend divergem; a base anterior foi mantida.');
 }
 return next;
}
