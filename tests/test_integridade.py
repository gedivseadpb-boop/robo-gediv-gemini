"""Testes isolados; exemplos sintéticos nunca são publicações reais."""
import copy
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
import fitz
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import robo
import dashboard
import revisar
import importar_historico
import comparar_indice

URL = 'https://auniao.pb.gov.br/servicos/doe/2026/outubro/exemplo.pdf'


def row(identifier, status='PENDENTE — conferir PDF'):
    return {'id': identifier, 'fonte': URL, 'data': '2026-10-01', 'resenha': '1/2026',
            'processo': 'SAD-PSE-2026/00001', 'servidor': 'PESSOA DE TESTE',
            'matricula': '000001', 'pagina': 3, 'eixo': 'Progressão',
            'modalidade': 'Vertical', 'grupo': 'GAJ', 'subcategoria': '',
            'resultado': 'Deferido', 'alteracao': 'Original', 'validacao': status,
            'trecho': 'Dado sintético de teste'}


def state(status='PROCESSADO COM PENDÊNCIAS', digest='abc'):
    return {'edicoes': [{'url': URL, 'data': '2026-10-01', 'status': status,
                         'arquivo_sha256': digest, 'pendencias': ['pendência']}],
            'registros': [row('old', 'VALIDADO')], 'eventos': [], 'atualizado_em': None}


class Integridade(unittest.TestCase):
    def test_parcial_nao_e_concluido(self):
        self.assertFalse(robo.completed({'status': 'PROCESSADO COM PENDÊNCIAS', 'pendencias': []}))
        self.assertFalse(robo.completed({'status': 'PROCESSADO', 'pendencias': ['falha']}))
        self.assertTrue(robo.completed({'status': 'PROCESSADO', 'pendencias': []}))

    def test_dominio_e_credenciais_validados(self):
        self.assertTrue(robo.official_url(URL))
        self.assertTrue(robo.official_url('https://www.auniao.pb.gov.br/servicos/doe'))
        for invalid in ['http://auniao.pb.gov.br/a', 'https://auniao.pb.gov.br.evil.test/a',
                        'https://auniao.pb.gov.br@evil.test/a',
                        'https://user:pass@auniao.pb.gov.br/a',
                        'https://auniao.pb.gov.br:8443/a']:
            self.assertFalse(robo.official_url(invalid), invalid)

    def test_redirecionamento_para_fora_nao_e_seguido(self):
        response = Mock(status_code=302, headers={'Location': 'https://outro.test/documento'})
        session = Mock(); session.get.return_value = response
        with patch.object(robo, 'requests', SimpleNamespace(RequestException=OSError)), \
             patch.object(robo.time, 'sleep'):
            with self.assertRaisesRegex(ValueError, 'Redirecionamento fora'):
                robo.fetch(URL, session)
        self.assertTrue(all(c.args[0] == URL for c in session.get.call_args_list))

    def test_reprocessamento_mesmo_pdf_conserva_revisao_e_candidatos(self):
        data = state()
        novo = row('new')
        substituto = row('old'); substituto['servidor'] = 'NOME ALTERADO SEM REVISÃO'
        meta = {'url': URL, 'data': '2026-10-01', 'status': 'PROCESSADO COM PENDÊNCIAS',
                'arquivo_sha256': 'abc', 'pendencias': ['ocr']}
        robo.update(data, meta, [substituto, novo], [])
        by_id = {r['id']: r for r in data['registros']}
        self.assertEqual(by_id['old']['servidor'], 'PESSOA DE TESTE')
        self.assertEqual(by_id['old']['validacao'], 'VALIDADO')
        self.assertEqual(by_id['new']['validacao'], 'PENDENTE — conferir PDF')
        self.assertEqual(data['edicoes'][0]['registros'], 2)

    def test_pdf_substituido_guarda_versao_antiga_e_mantem_pendencia(self):
        data = state()
        original = copy.deepcopy(data['registros'])
        meta = {'url': URL, 'data': '2026-10-01', 'status': 'PROCESSADO',
                'arquivo_sha256': 'def', 'pendencias': []}
        robo.update(data, meta, [row('new')], [])
        self.assertEqual(data['historico_versoes'][0]['registros'], original)
        self.assertEqual(data['edicoes'][0]['status'], 'PROCESSADO COM PENDÊNCIAS')
        self.assertTrue(data['edicoes'][0]['versao_alterada_pendente'])
        robo.update(data, meta, [row('new')], [])
        self.assertEqual(len(data['historico_versoes']), 1)
        self.assertFalse(robo.completed(data['edicoes'][0]))

    def test_reprocessamento_atualiza_candidato_ainda_nao_revisado(self):
        data = state(); data['registros'] = [row('old')]
        novo = row('old'); novo['servidor'] = 'EXTRAÇÃO ATUALIZADA'
        meta = {'url': URL, 'data': '2026-10-01', 'status': 'PROCESSADO COM PENDÊNCIAS',
                'arquivo_sha256': 'abc', 'pendencias': ['ocr']}
        robo.update(data, meta, [novo], [])
        self.assertEqual(data['registros'][0]['servidor'], 'EXTRAÇÃO ATUALIZADA')

    def test_painel_nao_promove_candidato_nem_evento_sem_vinculo(self):
        data = state(); data['registros'].append(row('new'))
        data['eventos'] = [{'id': 'ev', 'data': '2026-10-02', 'tipo': 'Retificação',
                            'validacao': 'VALIDADO', 'fonte': URL, 'pagina': 3}]
        adapted = dashboard.adapt_state(data)
        self.assertEqual(adapted['meta']['conferidos'], 1)
        self.assertEqual(adapted['meta']['pendentes'], 1)
        self.assertEqual(adapted['events'][0]['validation'], 'pendente')
        self.assertEqual(adapted['rows'][0]['group'], 'GAJ')

    def test_conferencia_previa_em_texto_indexado_nao_valida_registro(self):
        candidate=row('a'); candidate['conferencia_previa']='Comparado ao texto indexado; PDF ainda pendente.'
        adapted=dashboard.adapt_state({'registros':[candidate]})
        self.assertEqual(adapted['rows'][0]['preliminaryReview'],candidate['conferencia_previa'])
        self.assertEqual(adapted['rows'][0]['validation'],'pendente')
        self.assertEqual(adapted['meta']['conferidos'],0)

    def test_comparacao_indexada_preserva_estado_e_delimita_publicacao(self):
        a=row('a'); a['matricula']='123456-7'; a['resenha']='1/2026 · SEAD'
        b=row('b'); b.update(processo='SAD-PSE-2026/00002', matricula='234567-8',
                             servidor='NOME DIFERENTE')
        c=row('c'); c.update(processo='SAD-PSE-2026/00003', matricula='345678-9',
                             servidor='PESSOA DEPOIS')
        original={'registros':[a,b,c]}; before=copy.deepcopy(original)
        excerpt=('RESENHA 1/2026\nGERENCIA EXECUTIVA DE CONCESSAO DE DIREITOS E VANTAGENS\n'
                 'DEFERIU PROGRESSAO FUNCIONAL VERTICAL GAJ\n'
                 'SAD-PSE-2026/00001 123456-7 PESSOA DE TESTE TECNICO\n'
                 'SAD-PSE-2026/00002 234567-8 OUTRA PESSOA TECNICO\n'
                 'PUBLIQUE-SE\n'
                 'SAD-PSE-2026/00003 345678-9 PESSOA DEPOIS TECNICO\n')
        result, audit=comparar_indice.compare(original,excerpt,url=URL,edition='2026-10-01',
                    page=3,resenha='1/2026',consulted='2026-10-31')
        self.assertEqual(original,before)
        self.assertEqual(audit['registros_comparados'],1)
        self.assertEqual(audit['processos_no_recorte'],2)
        self.assertTrue(audit['gediv_expressa_no_recorte'])
        self.assertIn('conferencia_previa',result['registros'][0])
        self.assertNotIn('conferencia_previa',result['registros'][1])
        self.assertNotIn('conferencia_previa',result['registros'][2])
        self.assertTrue(all(r['validacao'].startswith('PENDENTE') for r in result['registros']))
        self.assertEqual(dashboard.adapt_state(result)['meta']['conferidos'],0)
        self.assertFalse(comparar_indice._same_resenha('11/2026 · SEAD','1/2026'))

    def test_comparacao_indexada_recusa_ambiguidade_e_fonte_nao_oficial(self):
        excerpt=('RESENHA 1/2026\nDEFERIU PROGRESSAO FUNCIONAL VERTICAL\n'
                 'SAD-PSE-2026/00001 123456-7 PESSOA DE TESTE TECNICO\n')
        params={'edition':'2026-10-01','page':3,'resenha':'1/2026','consulted':'2026-10-31'}
        with self.assertRaisesRegex(ValueError,'única vez'):
            comparar_indice.compare({'registros':[]},excerpt+excerpt,url=URL,**params)
        with self.assertRaisesRegex(ValueError,'oficial'):
            comparar_indice.compare({'registros':[]},excerpt,url='https://fora.test/doe.pdf',**params)

    def test_revisao_exige_conferencia_e_preserva_trilha(self):
        data = state(); data['registros'] = [row('new')]
        with self.assertRaisesRegex(ValueError, 'confirme a fonte'):
            revisar.review_record(data, 'new', 'VALIDADO', 'Revisor de teste',
                                   'Conferência documental registrada', False)
        self.assertEqual(data['registros'][0]['validacao'], 'PENDENTE — conferir PDF')
        revisar.review_record(data, 'new', 'VALIDADO', 'Revisor de teste',
                              'Conferência documental registrada', True)
        self.assertEqual(data['registros'][0]['validacao'], 'VALIDADO')
        self.assertEqual(data['revisoes'][0]['arquivo_sha256'], 'abc')
        self.assertEqual(dashboard.adapt_state(data)['meta']['conferidos'], 1)

    def test_revisao_bloqueia_versao_substituida_sem_conferencia(self):
        data = state(); data['registros'] = [row('new')]
        data['edicoes'][0]['versao_alterada_pendente'] = True
        with self.assertRaisesRegex(ValueError, 'versão substituída'):
            revisar.review_record(data, 'new', 'VALIDADO', 'Revisor de teste',
                                   'Conferência documental registrada', True)

    def test_importacao_preserva_origem_sem_promover_nem_somar_alteracao(self):
        original={'id':'origem','url':URL,'edition':'2026-10-01','page':3,
                  'resenha':'1/2026','process':'SAD-PSE-2026/00001','axis':'horizontal',
                  'modality':'horizontal','nature':'publicacao','result':'deferido',
                  'validation':'validado','gedivMention':'nao_expresso'}
        evento={**original,'id':'modificador','nature':'republicacao'}
        rejected={**original,'id':'rejeitado','validation':'rejeitado'}
        edition={'url':URL,'date':'2026-10-01','status':'parcial','hash':'abc'}
        imported=importar_historico.import_catalog({'records':[original,evento,rejected],
                                                     'editions':[edition]})
        self.assertEqual(len(imported['registros']),2)
        self.assertEqual(len(imported['eventos']),1)
        self.assertEqual(imported['registros'][0]['validacao_origem'],'validado')
        self.assertEqual(imported['registros'][0]['mencao_gediv_origem'],'nao_expresso')
        self.assertEqual(dashboard.validation(imported['registros'][0]['validacao']),'pendente')
        self.assertEqual(dashboard.validation(imported['registros'][1]['validacao']),'rejeitado')
        self.assertEqual(imported['eventos'][0]['validacao'],'PENDENTE_VINCULACAO')
        self.assertEqual(dashboard.adapt_state(imported)['meta']['conferidos'],0)

    def test_pagina_nao_confirmada_nao_se_transformar_em_link_exato(self):
        candidate=row('a'); candidate['pagina_confirmada_origem']=False
        self.assertIsNone(dashboard.adapt_state({'registros':[candidate]})['rows'][0]['page'])

    def test_painel_nao_confunde_resenhas_mesmo_numero_em_fontes_distintas(self):
        a=row('a', 'VALIDADO'); b=row('b', 'VALIDADO')
        b['fonte']='https://auniao.pb.gov.br/servicos/doe/2026/outubro/segundo.pdf'
        adapted=dashboard.adapt_state({'registros':[a,b]})
        self.assertNotEqual(adapted['rows'][0]['resenha_id'], adapted['rows'][1]['resenha_id'])

    def test_html_escapa_script_vindo_da_fonte(self):
        data = state(); data['registros'][0]['trecho'] = '</script><script>alert(1)</script>'
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            output = dashboard.build_interactive_html(data, root, d).read_text(encoding='utf-8')
        self.assertNotIn('</script><script>alert(1)</script>', output)
        self.assertIn('\\u003c/script\\u003e', output)
        self.assertNotIn('src="data.js"', output)

    def test_pdf_sintetico_percorre_coletor_estado_e_painel_sem_promocao(self):
        # PDF sintético só para teste local: não é uma publicação nem dado de produção.
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); pdf=root/'teste.pdf'; statefile=root/'estado.json'; out=root/'saida'
            doc=fitz.open(); page=doc.new_page(width=595,height=842)
            text=('GERENCIA EXECUTIVA DE CONCESSAO DE DIREITOS E VANTAGENS\n'
                  'RESENHA 1/2026\n'
                  'DEFERIU os processos de PROGRESSAO FUNCIONAL HORIZONTAL\n'
                  'Grupo Ocupacional de APOIO JUDICIARIO GAJ.\n'
                  'SAD-PSE-2026/12345 000001 PESSOA DE TESTE TECNICO\n'
                  'Documento sintetico exclusivamente para teste local.\n')
            page.insert_textbox(fitz.Rect(30,40,280,500),text,fontsize=8)
            doc.save(pdf); doc.close()
            with contextlib.redirect_stdout(io.StringIO()):
                robo.main(['--pdf',str(pdf),'--data-pdf','2026-10-01','--url-pdf',URL,
                           '--estado',str(statefile),'--saida',str(out)])
            result=json.loads(statefile.read_text()); aggregate=json.loads((out/'dados_agregados.json').read_text())
            self.assertEqual(len(result['registros']),1)
            self.assertEqual(aggregate['candidatos_pendentes'],1)
            self.assertEqual(aggregate['decisoes_validadas'],0)
            html=(out/'painel_gerencial_privado.html').read_text()
            self.assertIn('"validation":"pendente"',html)

    def test_varios_blocos_gediv_mesma_coluna_preservam_contexto(self):
        # Formato inspirado em edições oficiais, dados inteiramente sintéticos.
        with tempfile.TemporaryDirectory() as d:
            pdf=Path(d)/'teste.pdf'; doc=fitz.open(); page=doc.new_page(width=595,height=842)
            section=('SECRETARIA DE ESTADO DA ADMINISTRACAO\n'
                     'DIRETORIA EXECUTIVA DE RECURSOS HUMANOS\n'
                     'GERENCIA EXECUTIVA DE CONC. DE DIREITOS E VANTAGENS\n'
                     'RESENHA Nº : 138/2026 /DEREH/GS\n'
                     'INDEFERIR os processos de PROGRESSAO FUNCIONAL HORIZONTAL do Grupo ANS\n'
                     'SAD-PSE-2026/10001 123456-7 PESSOA UM TECNICO\n'
                     'SECRETARIA DE ESTADO DA ADMINISTRACAO\n'
                     'DIRETORIA EXECUTIVA DE RECURSOS HUMANOS\n'
                     'GERENCIA EXECUTIVA DE CONC. DE DIREITOS E VANTAGENS\n'
                     'RESENHA Nº : 139/2026 /DEREH/GS\n'
                     'DEFERIR os processos de PROGRESSAO FUNCIONAL VERTICAL do Grupo ESPECIAL\n'
                     'SAD-PSE-2026/10002 234567-8 PESSOA DOIS TECNICO\n'
                     'SECRETARIA DE ESTADO DE OUTRA AREA\n'
                     'GERENCIA EXECUTIVA DE OUTRA AREA\n'
                     'RESENHA Nº : 140/2026 /OUTRA\n'
                     'DEFERIR processo de PROGRESSAO FUNCIONAL HORIZONTAL\n'
                     'SAD-PSE-2026/10003 345678-9 PESSOA TRES TECNICO\n')
            page.insert_textbox(fitz.Rect(30,40,280,800),section,fontsize=6)
            doc.save(pdf); doc.close()
            rows,info=robo.pdf_to_records(pdf,'2026-10-01',URL)
        found={r['processo']:(r['resenha'],r['resultado'],r['modalidade']) for r in rows}
        self.assertEqual(found,{'SAD-PSE-2026/10001':('138/2026','Indeferido','Horizontal'),
                                'SAD-PSE-2026/10002':('139/2026','Deferido','Vertical')})
        self.assertEqual(info['resenhas'],2)

    def test_ocr_sem_linha_nao_atribui_registro_de_outra_area(self):
        # Não atribuir automaticamente à GEDIV texto vindo de outra área da página.
        section=('GERENCIA EXECUTIVA DE CONCESSAO DE DIREITOS E VANTAGENS\n'
                 'RESENHA 1/2026\nDEFERIU PROGRESSAO FUNCIONAL HORIZONTAL\n')
        unrelated='SAD-PSE-2026/10099 123456-7 PESSOA DE OUTRA AREA TECNICO'
        with tempfile.TemporaryDirectory() as d:
            pdf=Path(d)/'teste.pdf'; doc=fitz.open(); doc.new_page(); doc.save(pdf); doc.close()
            with patch.object(robo,'page_sections',return_value=[(section,True)]), \
                 patch.object(robo,'extract_rows_from_image',return_value=unrelated,create=True):
                rows,info=robo.pdf_to_records(pdf,'2026-10-01',URL)
        self.assertEqual(rows,[])
        self.assertTrue(info['pendencias'])

    def test_resenha_antes_do_cabecalho_nao_herda_bloco_anterior(self):
        text=robo.norm('GERENCIA EXECUTIVA DE CONCESSAO DE DIREITOS E VANTAGENS\n'
                       'RESENHA 111/2026\nINDEFERIU PROGRESSAO HORIZONTAL\n'
                       'SAD-PSE-2026/10001 123456-7 PESSOA UM TECNICO\n'
                       'Nº da Resenha : 222/2026\n'
                       'SECRETARIA DE ESTADO DA ADMINISTRACAO\n'
                       'GERENCIA EXECUTIVA DE CONCESSAO DE DIREITOS E VANTAGENS\n'
                       'DEFERIU PROGRESSAO VERTICAL\n'
                       'SAD-PSE-2026/10002 234567-8 PESSOA DOIS TECNICO\n')
        blocks=list(robo.gediv_blocks(text))
        self.assertEqual([[m.group(1) for m in robo.PAT_RES.finditer(block)] for block in blocks],
                         [['111/2026'],['222/2026']])

    def test_loop_retenta_pdf_parcial_com_mesmo_hash(self):
        body = b'%PDF-test-only'; digest = hashlib.sha256(body).hexdigest()
        data = state(digest=digest)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); statefile=root/'estado.json'
            statefile.write_text(json.dumps(data), encoding='utf-8')
            discovered=[{'url':URL, 'data':'2026-10-01'}]
            info={'paginas':1,'resenhas':1,'pendencias':['ocr'],'eventos':[]}
            fake_requests=SimpleNamespace(Session=Mock(return_value=Mock()))
            with patch.object(robo, 'ROOT', root), patch.object(robo, 'requests', fake_requests), \
                 patch.object(robo, 'discover', return_value=discovered), \
                 patch.object(robo, 'fetch', return_value=body), \
                 patch.object(robo, 'pdf_to_records', return_value=([row('new')], info)) as parser, \
                 patch.object(robo, 'build_html'):
                robo.main(['--inicio','2026-10-01','--fim','2026-10-01','--modo','historico',
                           '--estado',str(statefile),'--saida',str(root/'saida')])
            result=json.loads(statefile.read_text())
            self.assertEqual(parser.call_count, 1)
            self.assertEqual({r['id'] for r in result['registros']}, {'old','new'})
            self.assertEqual(result['cobertura']['edicoes_pendentes_intervalo'], 1)

    def test_falha_de_reprocessamento_nao_apaga_resultado(self):
        data = state()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); statefile=root/'estado.json'
            statefile.write_text(json.dumps(data), encoding='utf-8')
            fake_requests=SimpleNamespace(Session=Mock(return_value=Mock()))
            with patch.object(robo, 'ROOT', root), patch.object(robo, 'requests', fake_requests), \
                 patch.object(robo, 'discover', return_value=[{'url':URL,'data':'2026-10-01'}]), \
                 patch.object(robo, 'fetch', side_effect=ValueError('falha simulada')), \
                 patch.object(robo, 'build_html'):
                robo.main(['--inicio','2026-10-01','--fim','2026-10-01','--modo','historico',
                           '--estado',str(statefile),'--saida',str(root/'saida')])
            result=json.loads(statefile.read_text())
            self.assertEqual(result['registros'][0]['id'], 'old')
            self.assertFalse(robo.completed(result['edicoes'][0]))
            self.assertEqual(result['cobertura']['edicoes_pendentes_intervalo'], 1)

if __name__ == '__main__':
    unittest.main()
