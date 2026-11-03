#!/usr/bin/env python3
"""Revisão manual de um registro em arquivo de estado privado.

Este utilitário não consulta nem altera bancos de dados. Requer conferência
humana do PDF; não valida automaticamente conteúdo ou permissões.
"""
import argparse
from pathlib import Path
import robo


def review_record(state, record_id, decision, reviewer, reason, confirmed_source=False):
    if decision not in {'VALIDADO', 'REJEITADO'}:
        raise ValueError('Decisão de revisão inválida')
    reviewer, reason = reviewer.strip(), reason.strip()
    if not reviewer or len(reason) < 12:
        raise ValueError('Informe responsável e justificativa documental (mínimo 12 caracteres)')
    matches = [r for r in state.get('registros', []) if r.get('id') == record_id]
    if len(matches) != 1:
        raise ValueError('Identificador ausente ou duplicado; nenhuma revisão realizada')
    record = matches[0]
    edition = next((e for e in state.get('edicoes', []) if e.get('url') == record.get('fonte')), None)
    if decision == 'VALIDADO':
        required=('processo','servidor','matricula','resenha','trecho')
        if any(not str(record.get(field) or '').strip() for field in required):
            raise ValueError('Campos obrigatórios ausentes: processo, servidor, matrícula, resenha e evidência')
        if record.get('resultado') not in {'Deferido','Indeferido'}:
            raise ValueError('Resultado não informado ou ambíguo exige conferência antes da validação')
        try:
            page = int(record.get('pagina'))
        except (TypeError, ValueError):
            page = 0
        if not confirmed_source or not robo.official_url(record.get('fonte') or '') or page < 1:
            raise ValueError('Para validar, confirme a fonte oficial e informe página verificável')
        if not edition or not edition.get('arquivo_sha256'):
            raise ValueError('A edição precisa possuir hash do documento conferido')
        if edition.get('versao_alterada_pendente'):
            raise ValueError('A versão substituída exige análise documental antes da validação')
    previous = record.get('validacao', '')
    event = {'registro_id': record_id, 'de': previous, 'para': decision,
             'responsavel': reviewer, 'justificativa': reason, 'em': robo.now(),
             'fonte': record.get('fonte', ''), 'pagina': record.get('pagina'),
             'arquivo_sha256': edition.get('arquivo_sha256', '') if edition else ''}
    record['validacao'] = decision
    state.setdefault('revisoes', []).append(event)
    return event


def main(argv=None):
    parser = argparse.ArgumentParser(description='Conferência manual em estado privado')
    parser.add_argument('--estado', required=True, help='Caminho do JSON privado existente')
    parser.add_argument('--id', required=True, help='Identificador exato do registro')
    parser.add_argument('--decisao', required=True, choices=['validar', 'rejeitar'])
    parser.add_argument('--responsavel', required=True)
    parser.add_argument('--justificativa', required=True)
    parser.add_argument('--confirme-fonte', action='store_true',
                        help='Declara ter conferido o registro no PDF oficial e na página informada')
    parser.add_argument('--saida', help='Diretório privado opcional para regenerar os painéis')
    args = parser.parse_args(argv)
    path = Path(args.estado)
    if not path.is_file():
        parser.error('O arquivo de estado informado não existe')
    state = robo.read_state(path)
    try:
        review_record(state, args.id, 'VALIDADO' if args.decisao == 'validar' else 'REJEITADO',
                      args.responsavel, args.justificativa, args.confirme_fonte)
    except ValueError as exc:
        parser.error(str(exc))
    robo.save_state(state, path)
    if args.saida:
        robo.build_html(state, Path(args.saida))
    print('Revisão registrada no arquivo privado.')

if __name__ == '__main__':
    main()
