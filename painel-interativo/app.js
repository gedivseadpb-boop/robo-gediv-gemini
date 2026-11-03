(function(){'use strict';
const data=window.GEDIV_DATA, exp=window.GEDIV_EXPORT;
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const S={view:'geral',axis:'',modality:'',group:'',category:[],merit:'',query:'',from:'',to:'',card:'',mode:'resenha',page:0,selected:''};
const groupNames={'MAG':'MAG · Magistério','SAUDE':'Saúde','GAJ-1700':'GAJ · Apoio Judiciário','FAP-1300':'FAP · Fiscalização Agropecuária','TEC-ADM':'AST · Técnicos Administrativos','ANS-900':'ANS · Nível Superior','ESPECIAL':'Grupo Especial','DPS-1600':'DPS · Divulgação e Promoção','FAZENDA':'Fazenda · Auditor Fiscal','OSPB':'OSPB · Orquestra Sinfônica','GPC':'GPC · Polícia Civil','SEI':'SEI · Informática','SAT':'SAT · Área Tecnológica','ACI':'ACI · Auditoria e Controle Interno','PPGG':'PPGG · a validar'};
const backStack=[];let beforeToday=null;
function checkpoint(){backStack.push(JSON.parse(JSON.stringify(S)));try{history.pushState({gediv:true},'');}catch{} }
function restorePrevious(){if(!backStack.length)return;Object.assign(S,backStack.pop());$('#search').value=S.query;render();}
window.addEventListener('popstate',restorePrevious);
function toggleService(id){S.category=S.category.includes(id)?S.category.filter(x=>x!==id):[...S.category,id];}
function setSlice(key){if(key==='tempo'){S.axis='tempo';S.modality='';S.group='';S.view='tempo';}else{S.axis='progressao';S.modality=key==='vertical'?'Vertical':'Horizontal';S.category=[];S.view=key;}S.card='';S.page=0;S.selected='';}

const views={geral:['VISÃO GERAL','Visão geral das publicações','Explore os resultados e consulte cada publicação na fonte.'],vertical:['PROGRESSÃO VERTICAL','Progressão Funcional Vertical','Acompanhe os grupos ocupacionais e os resultados das publicações.'],horizontal:['PROGRESSÃO HORIZONTAL','Progressão Funcional Horizontal','Acompanhe os grupos ocupacionais e os resultados das publicações.'],tempo:['TEMPO DE SERVIÇO','Tempo de Serviço e Contribuição','Todos os serviços do catálogo permanecem visíveis nesta visão.'],outras:['OUTROS BENEFÍCIOS','Outros benefícios e publicações GEDIV','Área reservada para serviços adicionais, após identificação e validação documental.'],hoje:['PUBLICAÇÕES DO DIA','Publicações do dia','Resultados encontrados para a data selecionada na base disponível.'],historico:['HISTÓRICO','Histórico e tendências','Acompanhe as datas existentes na base e as alterações documentais.']};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const dt=d=>d?d.split('-').reverse().join('/'):'—';
const shortDate=d=>d?d.slice(5).split('-').reverse().join('/'):'—';
const uniq=(rows,key)=>new Set(rows.map(x=>x[key]).filter(Boolean)).size;
const dateOK=d=>(!S.from||d>=S.from)&&(!S.to||d<=S.to);
const catName=id=>data.categories.find(x=>x[0]===id)?.[1]||'Não informado';
const labelGroup=id=>groupNames[id]||id||'Grupo não informado';
const labelRow=r=>r.axis==='progressao'?'Progressão '+r.modality:catName(r.category);
const badge=r=>r.axis==='tempo'?'<span class="badge t">Tempo de Serviço</span>':r.modality==='Vertical'?'<span class="badge v">Vertical</span>':'<span class="badge h">Horizontal</span>';
const meritBadge=r=>'<span class="badge '+(r.merit==='indeferido'?'neg':'ok')+'">'+(r.merit==='indeferido'?'Indeferido':r.merit==='deferido'?'Deferido':'Outro')+'</span>';
function official(url,page){try{let u=new URL(url);if(u.protocol!=='https:'||u.hostname!=='auniao.pb.gov.br')return '';u.hash='page='+Number(page||1);return u.href;}catch{return '';}}
function matches(r){
 if(S.view==='outras')return false;
 if(S.axis&&r.axis!==S.axis)return false;
 if(S.modality&&(r.axis!=='progressao'||r.modality!==S.modality))return false;
 if(S.group&&(r.axis!=='progressao'||r.group!==S.group))return false;
 if(S.category.length&&(r.axis!=='tempo'||!S.category.includes(r.category)))return false;
 if(S.merit&&r.merit!==S.merit)return false;
 if(S.query&&!norm([r.resenha,r.process,r.server,r.registration,r.group,labelGroup(r.group),r.modality,catName(r.category)].join(' ')).includes(norm(S.query)))return false;
 return true;
}
function selectedEvents(type,base){let acts=new Set(base.map(r=>r.act));return data.events.filter(e=>e.validation==='conferido'&&dateOK(e.date)&&acts.has(e.act)&&(type==='refeitos'?['Retificação','Correção','Republicação'].includes(e.type):e.type==='Tornado sem efeito'));}
function model(){
 let dim=data.rows.filter(r=>r.validation==='conferido'&&matches(r)), original=dim.filter(r=>dateOK(r.date));
 let redo=selectedEvents('refeitos',dim),voided=selectedEvents('semEfeito',dim);
 let metrics={processes:uniq(original,'process'),resenhas:uniq(original,'resenha'),decisions:original.length,deferidos:original.filter(r=>r.merit==='deferido').length,indeferidos:original.filter(r=>r.merit==='indeferido').length,refeitos:new Set(redo.map(e=>e.act)).size,semEfeito:new Set(voided.map(e=>e.act)).size};
 let rows=original;
 if(S.card==='deferidos')rows=original.filter(r=>r.merit==='deferido');
 else if(S.card==='indeferidos')rows=original.filter(r=>r.merit==='indeferido');
 else if(S.card==='processes')rows=original.filter(r=>!!r.process);
 else if(S.card==='refeitos'||S.card==='semEfeito'){let acts=new Set((S.card==='refeitos'?redo:voided).map(e=>e.act));rows=dim.filter(r=>acts.has(r.act));}
 return {rows,metrics,redo,voided,original};
}
function groups(rows){let m=new Map();for(const r of rows){let key=S.mode==='resenha'?r.resenha:(r.process||'sem-id-'+r.id);if(!m.has(key))m.set(key,[]);m.get(key).push(r);}return [...m].map(([key,items])=>({key,items})).sort((a,b)=>b.items[0].date.localeCompare(a.items[0].date)||a.key.localeCompare(b.key));}
function sync(){
 $('#axis').value=S.axis;$('#modality').value=S.modality;$('#group').value=S.group;$('#merit').value=S.merit;$('#from').value=S.from;$('#to').value=S.to;
 $$('.tabs button').forEach(b=>b.classList.toggle('active',b.dataset.view===S.view));
 let v=views[S.view];$('#breadcrumb').textContent=v[0];$('#viewTitle').textContent=v[1];$('#viewSubtitle').textContent=v[2];
 $$('#serviceFilters button').forEach(b=>{let active=S.category.includes(b.dataset.cat);b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
 $('#byResenha').classList.toggle('active',S.mode==='resenha');$('#byProcess').classList.toggle('active',S.mode==='processo');
}
function kpis(m){let cards=[['resenhas','Resenhas',m.resenhas,m.resenhas===1?'publicação distinta':'publicações distintas','▤',''],['processes','Processos',m.processes,m.processes===1?'identificado':'identificados','▧',''],['decisions','Decisões',m.decisions,m.decisions===1?'linha individual':'linhas individuais','▥',''],['deferidos','Deferidos',m.deferidos,m.deferidos===1?'decisão conferida':'decisões conferidas','✓','green'],['indeferidos','Indeferidos',m.indeferidos,m.indeferidos===1?'decisão conferida':'decisões conferidas','×','red'],['refeitos','Refeitos',m.refeitos,m.refeitos===1?'ato com alteração':'atos com alteração','↻','amber'],['semEfeito','Sem efeito',m.semEfeito,'atos na amostra','⊘','red']];
 $('#kpis').innerHTML=cards.map(([id,label,value,sub,icon,color])=>`<button class="kpi ${color} ${S.card===id?'active':''}" data-card="${id}" title="Filtrar por ${esc(label)}"><span class="label">${esc(label)}</span><span class="marker">${icon}</span><b class="val">${data.meta.semBaseCarregada?'—':value}</b><span class="sub">${data.meta.semBaseCarregada?'Base não carregada':esc(sub)}</span></button>`).join('');
}
function timeline(rows){let dates=[...new Set(rows.map(r=>r.date))].sort(), shown=dates;let n=shown.map(day=>({day,v:rows.filter(r=>r.date===day&&r.modality==='Vertical').length,h:rows.filter(r=>r.date===day&&r.modality==='Horizontal').length,t:rows.filter(r=>r.date===day&&r.axis==='tempo').length}));let max=Math.max(1,...n.flatMap(q=>[q.v,q.h,q.t]));$('#timeline').innerHTML=n.length?n.map(q=>`<div class="time-col"><div class="bar-set">${[['v','vertical'],['h','horizontal'],['t','tempo']].map(([key,cl])=>`<button class="${cl}" data-day="${q.day}" data-series="${cl}" ${q[key]?'':'disabled'} title="${dt(q.day)} · ${cl}: ${q[key]}" style="height:${Math.max(q[key]?5:1,95*q[key]/max)}px"></button>`).join('')}</div><small>${shortDate(q.day)}</small></div>`).join(''):'<div class="empty-small">Nenhuma base carregada nesta cópia.</div>';
}
function donutPath(index, value, total, offset){
 const radius=52, circ=2*Math.PI*radius, visible=circ*value/total;
 return `<circle cx="70" cy="70" r="${radius}" fill="none" stroke="${index.color}" stroke-width="26" stroke-dasharray="${visible} ${circ-visible}" stroke-dashoffset="${-circ*offset/total}" transform="rotate(-90 70 70)" data-kind="${esc(index.kind)}" data-key="${esc(index.key)}" role="button" tabindex="0" aria-label="${esc(index.label)}: ${value} decisões, ${Math.round(100*value/total)}%" class="donut-slice"></circle>`;
}
function axisChart(rows){
 let list=[], title='Publicações por assunto',subtitle='Clique na fatia ou na legenda para detalhar';
 if(S.group||S.category.length){
  title='Resultados da seleção';subtitle='Clique em deferidos ou indeferidos';
  list=[['Deferidos','deferido','#17a675'],['Indeferidos','indeferido','#e86167']].map(([label,key,color])=>({label,key,color,kind:'merit',value:rows.filter(r=>r.merit===key).length}));
 }else if(S.axis==='tempo'){
  title='Tempo de Serviço por serviço';subtitle='Selecione um serviço para ver seus resultados';
  let colors=['#f49b45','#d36a44','#e0ad40','#d2866d','#bf6858','#e8be79','#a879bb'];
  list=data.categories.map(([key,label],i)=>({key,label,color:colors[i],kind:'category',value:rows.filter(r=>r.category===key).length}));
 }else if(S.axis==='progressao'&&S.modality){
  title='Progressão por grupo';subtitle='Selecione um grupo para ver seus resultados';
  let colors=['#2480f3','#16a788','#f49b45','#9b73d6','#dd6877','#3f9faa','#9a9d54','#7773bc','#e2b451','#b76e83','#368cc2','#64a770','#c77f47','#9c8dc2','#899eaf'];
  list=Object.entries(groupNames).map(([key,label],i)=>({key,label,color:colors[i%colors.length],kind:'group',value:rows.filter(r=>r.group===key).length})).filter(x=>x.value||x.key===S.group);
 }else{
  list=[['Vertical','vertical','#1265ef'],['Horizontal','horizontal','#13b88a'],['Tempo de Serviço','tempo','#ff973c']].map(([label,key,color])=>({label,key,color,kind:'axis',value:rows.filter(r=>key==='tempo'?r.axis==='tempo':(r.modality||'').toLowerCase()===key).length}));
 }
 $('#axisChartTitle').textContent=title;$('#axisChartSubtitle').textContent=subtitle;
 let n=list.reduce((a,x)=>a+x.value,0),offset=0;
 let circles=n?list.filter(x=>x.value).map(x=>{let result=donutPath(x,x.value,n,offset);offset+=x.value;return result;}).join(''):'<circle cx="70" cy="70" r="52" fill="none" stroke="#e7eef5" stroke-width="26"></circle>';
 $('#axisChart').innerHTML=`<div class="interactive-donut"><svg viewBox="0 0 140 140" role="group" aria-label="${esc(title)}">${circles}</svg><div class="donut-label"><b>${data.meta.semBaseCarregada?'—':n}</b><span>${n===1?'decisão':'decisões'}</span></div></div><div class="axis-legend">${list.map(x=>`<button data-kind="${esc(x.kind)}" data-key="${esc(x.key)}" aria-label="Selecionar ${esc(x.label)}, ${x.value} decisões"><i style="background:${x.color}"></i><span>${esc(x.label)} <b>${data.meta.semBaseCarregada?'—':x.value}</b>${n?' · '+Math.round(100*x.value/n)+'%':''}</span></button>`).join('')||'<small>Nenhuma base carregada nesta cópia.</small>'}</div>`;
}
function serviceBars(rows){
 let tempo=rows.filter(r=>r.axis==='tempo'),max=Math.max(1,...data.categories.map(c=>tempo.filter(r=>r.category===c[0]).length));
 $('#serviceBars').innerHTML=data.categories.map(([id,label])=>{let items=tempo.filter(r=>r.category===id),n=items.length,d=items.filter(r=>r.merit==='deferido').length,i=items.filter(r=>r.merit==='indeferido').length;return `<div class="service-row ${S.category.includes(id)?'selected-row':''}"><button class="service-name" data-cat="${id}" title="Selecionar ${esc(label)}">${esc(label)}</button><button class="result-track" data-cat="${id}" aria-label="${esc(label)}: ${d} deferidos e ${i} indeferidos na amostra"><span class="part good" style="width:${d*100/max}%"></span><span class="part bad" style="width:${i*100/max}%"></span></button><span class="service-value ${n?'':'pending'}">${n?`${d} def. · ${i} ind.`:'sem base carregada'}</span></div>`;}).join('');
}
function groupChart(rows){
 let progress=rows.filter(r=>r.axis==='progressao'),max=Math.max(1,...Object.keys(groupNames).map(id=>progress.filter(r=>r.group===id).length));
 $('#groupChart').innerHTML=Object.entries(groupNames).map(([id,name])=>{let items=progress.filter(r=>r.group===id),d=items.filter(r=>r.merit==='deferido').length,i=items.filter(r=>r.merit==='indeferido').length,n=items.length;return `<button class="group-row ${S.group===id?'selected-row':''}" data-group="${esc(id)}" aria-label="${esc(name)}: ${d} deferidos e ${i} indeferidos na amostra"><span>${esc(name)}</span><span class="result-track"><span class="part good" style="width:${d*100/max}%"></span><span class="part bad" style="width:${i*100/max}%"></span></span><b>${n?`${d} D · ${i} I`:'—'}</b></button>`;}).join('');
}
function resultsChart(rows){
 let all=[['Horizontal','horizontal'],['Vertical','vertical'],['Tempo de Serviço','tempo']],max=Math.max(1,...all.map(([l,k])=>rows.filter(r=>k==='tempo'?r.axis==='tempo':(r.modality||'').toLowerCase()===k).length));
 $('#resultsChart').innerHTML=all.map(([label,key])=>{let rr=rows.filter(r=>key==='tempo'?r.axis==='tempo':(r.modality||'').toLowerCase()===key),d=rr.filter(r=>r.merit==='deferido').length,i=rr.filter(r=>r.merit==='indeferido').length;return `<div class="result-line"><span>${label}</span><div class="result-track"><button class="part good" data-series="${key}" data-merit="deferido" style="width:${d*100/max}%" aria-label="${label}: ${d} deferidos" ${d?'':'disabled'}></button><button class="part bad" data-series="${key}" data-merit="indeferido" style="width:${i*100/max}%" aria-label="${label}: ${i} indeferidos" ${i?'':'disabled'}></button></div><b>${rr.length?`${d} D · ${i} I`:'sem dados'}</b></div>`;}).join('')+'<div class="result-key"><span><i class="good"></i>Deferidos</span><span><i class="bad"></i>Indeferidos</span></div>';
}
function activeFilters(){
 const chips=[];if(S.from||S.to)chips.push(['period',`Período: ${dt(S.from)} a ${dt(S.to)}`]);if(S.axis)chips.push(['axis',S.axis==='tempo'?'Tempo de Serviço':'Progressão']);if(S.modality)chips.push(['modality',S.modality]);if(S.group)chips.push(['group',labelGroup(S.group)]);for(const id of S.category)chips.push(['cat:'+id,catName(id)]);if(S.merit)chips.push(['merit',S.merit==='deferido'?'Deferido':S.merit==='indeferido'?'Indeferido':S.merit]);if(S.query)chips.push(['query','Busca: '+S.query]);if(S.card)chips.push(['card','Indicador selecionado']);
 $('#activeFilters').innerHTML=chips.length?'<span>Filtros ativos</span>'+chips.map(([key,label])=>`<button data-remove="${esc(key)}" aria-label="Remover filtro ${esc(label)}">${esc(label)} <b>×</b></button>`).join('')+'<button class="clear-inline" data-remove="all">Limpar todos</button>':'<span>Nenhuma base carregada nesta cópia</span>';
 $('#backView').disabled=!backStack.length;
}
function records(rows){let g=groups(rows),pages=Math.max(1,Math.ceil(g.length/5));S.page=Math.max(0,Math.min(S.page,pages-1));let shown=g.slice(S.page*5,S.page*5+5);if(!shown.some(x=>x.key===S.selected))S.selected=shown[0]?.key||'';
 $('#listHeading').textContent=S.mode==='resenha'?'RESENHA / ASSUNTO':'PROCESSO / SERVIDOR';$('#resultCount').textContent=`${rows.length} ${rows.length===1?'decisão':'decisões'} · ${uniq(rows,'resenha')} ${uniq(rows,'resenha')===1?'resenha':'resenhas'} · ${uniq(rows,'process')} ${uniq(rows,'process')===1?'processo identificado':'processos identificados'}`;
 $('#records').innerHTML=shown.length?shown.map(x=>{let r=x.items[0],label=S.mode==='resenha'?'Resenha '+r.resenha:(r.process||'Processo não transcrito'),sub=S.mode==='resenha'?`${dt(r.date)} · ${labelRow(r)}`:`${r.server} · Resenha ${r.resenha}`;return `<button class="record ${S.selected===x.key?'selected':''}" data-select="${esc(x.key)}"><span><b>${esc(label)}</b><small>${esc(sub)}</small><small>${badge(r)}</small></span><span class="qty">${x.items.length} ›</span></button>`;}).join(''):`<div class="empty-small">Nenhuma ocorrência no recorte carregado.<br>A cobertura histórica ainda está pendente.</div>`;
 $('#pagination').textContent=g.length?`${S.page*5+1}–${Math.min((S.page+1)*5,g.length)} de ${g.length}`:'0 registros';$('#prev').disabled=S.page===0;$('#next').disabled=S.page>=pages-1;
 let sel=g.find(x=>x.key===S.selected);details(sel);
}
function details(sel){if(!sel){$('#details').innerHTML='<div class="empty-small">Selecione uma publicação para ver os detalhes.</div>';return;}let r=sel.items[0],ev=data.events.filter(e=>e.act===r.act&&e.validation==='conferido'),url=official(r.url,r.page);$('#details').innerHTML=`<div class="detail-grid"><span class="dt">Publicação</span><span class="dd">${dt(r.date)}</span><span class="dt">Resenha</span><span class="dd">${esc(r.resenha)}</span><span class="dt">Assunto</span><span class="dd">${esc(labelRow(r))}</span><span class="dt">Grupo</span><span class="dd">${esc(r.axis==='progressao'?labelGroup(r.group):'—')}</span><span class="dt">Resultado</span><span class="dd">${meritBadge(r)}</span><span class="dt">Decisões</span><span class="dd">${sel.items.length} nesta seleção</span><span class="dt">Página DOE</span><span class="dd">${esc(r.page)}</span><span class="dt">Alterações</span><span class="dd">${ev.length?esc(ev[0].type)+' em '+dt(ev[0].date):'Não identificada na amostra'}</span></div><div class="detail-actions">${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">↗ Abrir PDF oficial</a>`:''}<button id="showDetails">Ver processos / histórico</button></div>`;$('#showDetails')?.addEventListener('click',()=>detailDialog(sel));}
function detailDialog(sel){let r=sel.items[0],events=data.events.filter(e=>e.act===r.act);let body=`<p>Resenha <b>${esc(r.resenha)}</b> · ${esc(labelRow(r))} · ${dt(r.date)}.</p><table class="dialog-table"><thead><tr><th>Processo</th><th>Servidor</th><th>Resultado</th></tr></thead><tbody>${sel.items.map(x=>`<tr><td>${esc(x.process||'Não transcrito')}</td><td>${esc(x.server)}</td><td>${meritBadge(x)}</td></tr>`).join('')}</tbody></table>`;if(events.length)body+=`<p><b>Histórico documental</b></p>${events.map(e=>`<p>${esc(e.type)} em ${dt(e.date)}: ${esc(e.description)} ${official(e.url,e.page)?`<a target="_blank" rel="noopener noreferrer" href="${esc(official(e.url,e.page))}">Abrir publicação da alteração</a>`:''}</p>`).join('')}`;openDialog('Processos e histórico',body);}
function render(){sync();let m=model();kpis(m.metrics);timeline(m.rows);axisChart(m.rows);resultsChart(m.rows);serviceBars(m.rows);groupChart(m.rows);records(m.rows);activeFilters();}
function reset(){Object.assign(S,{view:'geral',axis:'',modality:'',group:'',category:[],merit:'',query:'',from:'',to:'',card:'',page:0,selected:''});$('#search').value='';render();}
function nav(view){checkpoint();if(S.view==='hoje'&&view!=='hoje'&&beforeToday){S.from=beforeToday.from;S.to=beforeToday.to;beforeToday=null;}if(view==='hoje'&&S.view!=='hoje')beforeToday={from:S.from,to:S.to};S.view=view;S.axis='';S.modality='';S.group='';S.category=[];S.card='';S.page=0;S.selected='';if(view==='tempo')S.axis='tempo';if(view==='vertical'||view==='horizontal'){S.axis='progressao';S.modality=view==='vertical'?'Vertical':'Horizontal';}if(view==='hoje'){let today=new Date().toLocaleDateString('en-CA',{timeZone:'America/Fortaleza'});S.from=today;S.to=today;}render();}

function openDialog(title,body){$('#dialogTitle').textContent=title;$('#dialogBody').innerHTML=body;$('#dialog').showModal();}
function toast(s){let el=$('#toast');el.textContent=s;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),3000);}
function filterText(){return [views[S.view][1],S.from?'De '+dt(S.from):'',S.to?'Até '+dt(S.to):'',S.modality,S.group?labelGroup(S.group):'',S.category.length?S.category.map(catName).join(', '):'',S.merit,S.query?'Busca: '+S.query:''].filter(Boolean).join(' · ');}
function exportRows(){let m=model(),list=groups(m.rows);return list.map(x=>{let r=x.items[0];return [S.mode==='resenha'?r.resenha:(r.process||'Não transcrito'),labelRow(r),r.merit,dt(r.date),x.items.length];});}
function decisionRows(){let m=model();return [['Data da publicação','Resenha','Processo','Servidor (iniciais)','Eixo','Modalidade','Grupo','Serviço','Resultado','Página','Fonte'],...m.rows.map(r=>[dt(r.date),r.resenha,r.process||'Não transcrito',r.server,r.axis,r.modality||'',labelGroup(r.group),r.category?catName(r.category):'',r.merit,r.page,r.url])];}
function exportXlsx(){let m=model(),summary=[['Visão',views[S.view][1]],['Filtros',filterText()],['Cobertura',data.meta.coverage],['Atualização',data.meta.automation],[],['Indicador','Valor'],...Object.entries(m.metrics)],list=[['Resenha / processo','Assunto','Resultado','Data','Quantidade'],...exportRows()];exp.download(exp.xlsx({'Resumo':summary,'Visão selecionada':list,'Decisões':decisionRows()}),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','GEDIV-visao-selecionada.xlsx');toast('Planilha da visão selecionada gerada.');}
function exportCsv(){exp.download(exp.csv(decisionRows()),'text/csv;charset=utf-8','GEDIV-decisoes-filtradas.csv');toast('Lista filtrada gerada.');}
function exportPng(){let m=model();exp.png({title:views[S.view][1],filters:filterText(),metrics:m.metrics,records:exportRows(),coverage:data.meta.coverage});toast('Resumo da visão gerado.');}
function bind(){
 $('#serviceFilters').innerHTML=data.categories.map(([id,label])=>`<button data-cat="${id}" title="${esc(label)}"><i></i><span>${esc(label)}</span></button>`).join('');
 $('#group').innerHTML='<option value="">Todos os grupos</option>'+Object.entries(groupNames).map(([id,name])=>`<option value="${esc(id)}">${esc(name)}</option>`).join('');
 for(const id of ['axis','modality','group','merit','from','to'])$('#'+id).addEventListener('change',e=>{checkpoint();S[id]=e.target.value;S.card='';S.page=0;if(id==='axis'){S.view=S.axis==='tempo'?'tempo':'geral';S.category=[];S.modality='';S.group='';}if(id==='modality'&&S.modality){S.axis='progressao';S.category=[];S.view=S.modality==='Vertical'?'vertical':'horizontal';}if(id==='group'&&S.group){S.axis='progressao';S.category=[];if(S.view==='tempo')S.view=S.modality==='Vertical'?'vertical':S.modality==='Horizontal'?'horizontal':'geral';}render();});
 $('#search').addEventListener('input',e=>{S.query=e.target.value;S.page=0;S.card='';render();});
 $('#clear').addEventListener('click',()=>{checkpoint();reset();});$$('.tabs button').forEach(b=>b.addEventListener('click',()=>nav(b.dataset.view)));
 function chooseService(id){checkpoint();toggleService(id);S.axis='tempo';S.view='tempo';S.modality='';S.group='';S.card='';S.page=0;render();}
 $('#serviceFilters').addEventListener('click',e=>{let b=e.target.closest('[data-cat]');if(b)chooseService(b.dataset.cat);});
 $('#serviceBars').addEventListener('click',e=>{let b=e.target.closest('[data-cat]');if(b)chooseService(b.dataset.cat);});
 $('#groupChart').addEventListener('click',e=>{let b=e.target.closest('[data-group]');if(!b)return;checkpoint();S.axis='progressao';S.view=S.modality==='Vertical'?'vertical':S.modality==='Horizontal'?'horizontal':'geral';S.group=S.group===b.dataset.group?'':b.dataset.group;S.category=[];S.card='';S.page=0;render();});
 function pieSelect(b){let kind=b.dataset.kind,key=b.dataset.key;if(kind==='axis'){nav(key);return;}checkpoint();if(kind==='group'){S.group=S.group===key?'':key;S.axis='progressao';}if(kind==='category'){toggleService(key);S.axis='tempo';S.view='tempo';}if(kind==='merit')S.merit=S.merit===key?'':key;S.card='';S.page=0;render();}
 $('#axisChart').addEventListener('click',e=>{let b=e.target.closest('[data-kind]');if(b)pieSelect(b);});
 $('#axisChart').addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('circle[data-kind]')){e.preventDefault();pieSelect(e.target);}});
 $('#resultsChart').addEventListener('click',e=>{let b=e.target.closest('[data-series]');if(!b)return;checkpoint();setSlice(b.dataset.series);S.merit=S.merit===b.dataset.merit?'':b.dataset.merit;render();});
 $('#timeline').addEventListener('click',e=>{let b=e.target.closest('[data-day]');if(!b||b.disabled)return;checkpoint();S.from=b.dataset.day;S.to=b.dataset.day;setSlice(b.dataset.series);render();});
 $('#backView').addEventListener('click',()=>{if(!backStack.length)return;try{history.back();}catch{restorePrevious();}});
 $('#activeFilters').addEventListener('click',e=>{let b=e.target.closest('[data-remove]');if(!b)return;checkpoint();let key=b.dataset.remove;if(key==='all'){reset();return;}if(key==='period'){S.from='';S.to='';}else if(key==='axis'){S.axis='';S.modality='';S.group='';S.category=[];S.view='geral';}else if(key.startsWith('cat:'))S.category=S.category.filter(x=>x!==key.slice(4));else if(key==='query'){S.query='';$('#search').value='';}else S[key]='';S.page=0;render();});
 $('#kpis').addEventListener('click',e=>{let b=e.target.closest('[data-card]');if(!b)return;checkpoint();S.card=S.card===b.dataset.card?'':b.dataset.card;S.page=0;S.selected='';render();});
 $('#records').addEventListener('click',e=>{let b=e.target.closest('[data-select]');if(b){S.selected=b.dataset.select;records(model().rows);}});
 $('#byResenha').addEventListener('click',()=>{S.mode='resenha';S.page=0;S.selected='';render();});$('#byProcess').addEventListener('click',()=>{S.mode='processo';S.page=0;S.selected='';render();});$('#prev').addEventListener('click',()=>{S.page--;S.selected='';records(model().rows);});$('#next').addEventListener('click',()=>{S.page++;S.selected='';records(model().rows);});
 function hideSidebar(){$('#shell').classList.remove('mobile-open');$('#shell').classList.add('is-collapsed');} $('#collapse').addEventListener('click',hideSidebar);$('#collapseBottom').addEventListener('click',hideSidebar);$('#expand').addEventListener('click',()=>{$('#shell').classList.remove('is-collapsed');$('#shell').classList.add('mobile-open');});
 $('#downloadToggle').addEventListener('click',()=>{let menu=$('#downloadMenu');menu.hidden=!menu.hidden;$('#downloadToggle').setAttribute('aria-expanded',String(!menu.hidden));});
 $('#downloadXlsx').addEventListener('click',exportXlsx);$('#downloadCsv').addEventListener('click',exportCsv);$('#downloadPng').addEventListener('click',exportPng);$('#downloadPdf').addEventListener('click',()=>{let m=model();$('#printReport').innerHTML='<h3>Decisões da visão selecionada</h3><p>'+esc(filterText())+'</p><table><thead><tr><th>Data</th><th>Resenha</th><th>Processo</th><th>Servidor</th><th>Assunto</th><th>Resultado</th></tr></thead><tbody>'+m.rows.map(r=>'<tr><td>'+esc(dt(r.date))+'</td><td>'+esc(r.resenha)+'</td><td>'+esc(r.process||'Não transcrito')+'</td><td>'+esc(r.server)+'</td><td>'+esc(labelRow(r))+'</td><td>'+esc(r.merit)+'</td></tr>').join('')+'</tbody></table>';window.print();});
 $('#coverageOpen').addEventListener('click',()=>openDialog('Fontes e cobertura',`<p><b>Base parcial:</b> ${esc(data.meta.coverage)}</p><p>${esc(data.meta.automation)}</p><p>Os totais usam apenas decisões com vínculo GEDIV conferido. As demais permanecem separadas. Um serviço sem registros nesta amostra está com <b>cobertura pendente</b>, não com inexistência comprovada.</p><p>Nenhuma edição está carregada nesta cópia. Os números não representam a produção da GEDIV.</p>`));
 $('#about').addEventListener('click',()=>$('#coverageOpen').click());
 $('#showPending').addEventListener('click',()=>{let r=data.rows.filter(x=>x.validation==='pendente');openDialog('Registros em validação',`<p>Esses registros não entram nos indicadores enquanto o vínculo institucional não estiver comprovado.</p><table class="dialog-table"><tr><th>Resenha</th><th>Assunto</th><th>Pendência</th></tr>${r.map(x=>`<tr><td>${esc(x.resenha)}</td><td>${esc(labelRow(x))}</td><td>${esc(x.evidence)}</td></tr>`).join('')}</table>`);});
 $('#full').addEventListener('click',()=>{let rows=model().rows;openDialog('Publicações e processos',`<p>${rows.length} decisões na visão e filtros selecionados.</p><table class="dialog-table"><thead><tr><th>Resenha</th><th>Processo</th><th>Servidor</th><th>Assunto</th><th>Resultado</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.resenha)}</td><td>${esc(r.process||'Não transcrito')}</td><td>${esc(r.server)}</td><td>${esc(labelRow(r))}</td><td>${meritBadge(r)}</td></tr>`).join('')}</tbody></table>`);});
 $('#closeDialog').addEventListener('click',()=>$('#dialog').close());$('#closeDialog2').addEventListener('click',()=>$('#dialog').close());
 document.addEventListener('click',e=>{if(!e.target.closest('.downloads')){$('#downloadMenu').hidden=true;$('#downloadToggle').setAttribute('aria-expanded','false');}});
}
bind();render();
})();
