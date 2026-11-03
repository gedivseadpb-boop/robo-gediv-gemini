#!/usr/bin/env python3
"""Adapta catálogo histórico anterior para revisão, sem validar GEDIV automaticamente.

A saída é um arquivo privado novo; nunca é gravada na versão anterior nem em banco.
"""
import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
import robo

SUBCATEGORIES = {
    'anotacao': 'Anotação de Tempo',
    'desaverbacao': 'Desaverbação',
    'licenca_particular': 'Licença para Interesses Particulares',
    'desistencia': 'Desistência de Licença',
    'licenca_especial': 'Licença Especial',
    'conversao_licenca': 'Conversão de Licença Especial',
    'conversao_ferias': 'Conversão de Férias',
}
EVENT_TYPES = {'republicacao': 'Republicação', 'retificacao': 'Retificação',
               'correcao': 'Correção', 'tornado_sem_efeito': 'Tornado sem efeito'}


def import_catalog(archive):
    if not isinstance(archive, dict) or not isinstance(archive.get('records'), list) \
            or not isinstance(archive.get('editions'), list):
        raise ValueError('O catálogo precisa conter listas records e editions')
    result = {'edicoes': [], 'registros': [], 'eventos': [], 'historico_versoes': [],
              'revisoes': [], 'atualizado_em': robo.now(),
              'importacao': {'revisao_origem': archive.get('revision'),
                             'origem_preparada_em': archive.get('preparedAt'),
                             'inicio_origem': archive.get('from'), 'fim_origem': archive.get('to')}}
    for edition in archive['editions']:
        if not isinstance(edition, dict):
            raise ValueError('Edição inválida no catálogo de origem')
        status = str(edition.get('status') or '')
        # Estados da versão antiga não comprovam cobertura completa no novo escopo.
        mapped = 'ERRO' if status == 'falha' else 'PROCESSADO COM PENDÊNCIAS'
        meta = {'url': edition.get('url', ''), 'data': edition.get('date', ''),
                'status': mapped, 'paginas': edition.get('pages', 0),
                'registros': edition.get('records', 0),
                'pendencias': ['Catálogo anterior: cobertura e vínculo GEDIV exigem revisão.'],
                'estado_origem': status, 'tentativas_origem': edition.get('attempts', 0),
                'dados_origem': edition}
        if edition.get('hash'):
            meta['arquivo_sha256'] = edition['hash']
        result['edicoes'].append(meta)
    used = Counter()
    for item in archive['records']:
        if not isinstance(item, dict):
            raise ValueError('Registro inválido no catálogo de origem')
        canonical = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:20]
        used[digest] += 1
        identifier = 'historico-' + digest + (f'-{used[digest]}' if used[digest] > 1 else '')
        source = str(item.get('url') or '')
        # Preservar o estado anterior para auditoria, sem promovê-lo aos cartões.
        prior = str(item.get('validation') or '')
        rejected = robo.norm(prior) in {'REJEITADO', 'REJEITADA'}
        common = {'id': identifier, 'data': str(item.get('edition') or ''),
                  'fonte': source, 'pagina': item.get('page'),
                  'trecho': str(item.get('quote') or ''),
                  'validacao_origem': prior, 'id_origem': str(item.get('id') or ''),
                  'mencao_gediv_origem': str(item.get('gedivMention') or ''),
                  'pagina_confirmada_origem': item.get('pageConfirmed') is True,
                  'fonte_oficial_sintaxe': robo.official_url(source),
                  'dados_origem': item}
        nature = str(item.get('nature') or 'publicacao')
        if nature != 'publicacao':
            result['eventos'].append({**common, 'resenha_modificadora': str(item.get('resenha') or ''),
                'tipo': EVENT_TYPES.get(nature, 'Outro evento a revisar'),
                'validacao': 'REJEITADO' if rejected else 'PENDENTE_VINCULACAO'})
            continue
        axis = str(item.get('axis') or '')
        modality = str(item.get('modality') or '')
        if axis in {'vertical', 'horizontal'} or modality in {'vertical', 'horizontal'}:
            area, mode, sub = 'Progressão', (modality if modality in {'vertical', 'horizontal'} else axis).capitalize(), ''
        elif axis == 'tempo':
            area, mode, sub = 'Tempo de Serviço', '', SUBCATEGORIES.get(modality, '')
        else:
            area, mode, sub = 'Outras publicações GEDIV', '', ''
        merit = {'deferido': 'Deferido', 'indeferido': 'Indeferido'}.get(str(item.get('result') or '').lower(), 'Não informado')
        if used[digest]>1:
            common['duplicidade_pendente']=True
            common['conferencia_previa']='Ocorrência idêntica no catálogo anterior; conferir duplicidade.'
        result['registros'].append({**common, 'resenha': str(item.get('resenha') or ''),
            'processo': str(item.get('process') or ''), 'servidor': str(item.get('server') or ''),
            'matricula': str(item.get('registration') or ''), 'eixo': area, 'modalidade': mode,
            'grupo': '', 'subcategoria': sub, 'resultado': merit, 'alteracao': 'Original',
            'extracao': 'Curadoria anterior',
            'validacao': 'REJEITADO' if rejected else 'PENDENTE — conferir vínculo GEDIV e PDF'})
    result['cobertura'] = {'inicio': archive.get('from'), 'fim': archive.get('to'),
                           'edicoes_descobertas': len(result['edicoes']),
                           'edicoes_processadas_intervalo': 0,
                           'edicoes_pendentes_intervalo': len(result['edicoes']),
                           'ultima_execucao_erros': sum(e['status'] == 'ERRO' for e in result['edicoes'])}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='Importar cópia histórica para conferência privada')
    parser.add_argument('--origem', required=True, help='JSON histórico já disponível localmente')
    parser.add_argument('--estado-novo', required=True, help='Novo JSON privado; não substitui arquivos existentes')
    parser.add_argument('--saida', help='Diretório privado opcional para o painel de conferência')
    args = parser.parse_args(argv)
    source, destination = Path(args.origem), Path(args.estado_novo)
    if not source.is_file():
        parser.error('Arquivo de origem não encontrado')
    try:
        state = import_catalog(json.loads(source.read_text(encoding='utf-8')))
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        parser.error('Destino já existe; informe um novo arquivo para não sobrescrever')
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
    if args.saida:
        robo.build_html(state, Path(args.saida))
    print(f"Importados {len(state['registros'])} registros e {len(state['eventos'])} eventos; "
          'nenhum foi promovido automaticamente a decisão validada.')

if __name__ == '__main__':
    main()
