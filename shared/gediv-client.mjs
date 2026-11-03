import {acceptDashboardSnapshot, dashboardModel} from './dashboard-model.mjs';
export {dashboardModel};

export function validateSnapshot(value) {
  acceptDashboardSnapshot(value);
  if (value.rows.length > 50000 || value.events.length > 50000) throw Error('Resposta acima do limite.');
  const ids = new Set();
  for (const row of value.rows) {
    if (!row || typeof row.id !== 'string' || ids.has(row.id) ||
        !['pendente','conferido','rejeitado'].includes(row.validation) ||
        !['id','date','resenha','resenha_id','process','server','axis','url'].every(k => typeof row[k] === 'string') ||
        !/^\d{4}-\d{2}-\d{2}$/.test(row.date) || !(row.page === null || Number.isInteger(row.page) && row.page >= 0)) {
      throw Error('Registro incompatível; a leitura anterior foi mantida.');
    }
    const source = new URL(row.url);
    if (source.origin !== 'https://auniao.pb.gov.br' || !source.pathname.startsWith('/servicos/doe/')) {
      throw Error('Fonte documental incompatível.');
    }
    ids.add(row.id);
  }
  const counts = value.dashboard.counts;
  for (const [key, scope] of [['pending','pendente'],['confirmed','conferido'],['rejected','rejeitado']]) {
    if (counts[key] !== value.rows.filter(row => row.validation === scope).length) throw Error('Situações inconsistentes.');
  }
  for (const scope of ['pendente','conferido']) {
    const expected = dashboardModel(value, {validation:scope});
    const actual = value.dashboard.views[scope];
    for (const [key, metric] of Object.entries(expected.metrics)) {
      if (actual.metrics[key] !== metric) throw Error('Indicadores inconsistentes.');
    }
    for (const [key, count] of Object.entries(expected.series)) {
      if (actual.series[key] !== count) throw Error('Gráficos inconsistentes.');
    }
  }
  return value;
}

export async function fetchSnapshot({fetcher=fetch, signal}={}) {
  const response = await fetcher('/api/gediv/data', {
    method:'GET', credentials:'same-origin', cache:'no-store', signal,
    headers:{Accept:'application/json'}, redirect:'error'
  });
  if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) {
    throw Error(response.status === 403 ? 'Acesso restrito. Entre com sua conta autorizada.' : 'Não foi possível atualizar. A leitura anterior foi mantida.');
  }
  return validateSnapshot(await response.json());
}

// Publicação e validação documental são campos distintos. Nunca promove candidatos.
export function legacyView(snapshot, scope=snapshot.dashboard.defaultScope) {
  const model = dashboardModel(snapshot, {validation:scope});
  const categories = new Map(snapshot.categories);
  const records = model.rows.map(r => ({
    data:r.date, resenha:r.resenha, resenha_id:r.resenha_id, servidor:r.server,
    matricula:r.registration||'', processo:r.process, processo_key:r.process,
    eixo:r.axis==='tempo'?'Tempo de Serviço':'Progressão', modalidade:r.modality||'',
    subcategoria:categories.get(r.category)||'', grupo:r.group||'Não informado',
    resultado:r.merit==='deferido'?'Deferido':r.merit==='indeferido'?'Indeferido':'Não informado',
    fonte:r.url, pagina:r.page, act:r.act||'', validation:r.validation,validacao:r.validation
  }));
  return {records, events:model.scope==='conferido'?snapshot.events.filter(e=>e.validation==='conferido'&&e.act):[], model};
}
