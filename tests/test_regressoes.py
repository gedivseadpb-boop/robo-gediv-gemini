#!/usr/bin/env python3
"""Auditoria isolada do código GEDIV; fixtures inteiramente sintéticas.

Não acessa rede, banco, GitHub ou site hospedado. O código do projeto é importado
de --source. Falhas são requisitos não atendidos, não corrigidos pelo teste.
"""
import argparse
import contextlib
import copy
import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import fitz

ARGS=SimpleNamespace(source=Path(__file__).resolve().parents[1])
sys.path.insert(0,str(ARGS.source/'src'))
import robo
import dashboard
import importar_historico
import revisar

URL='https://auniao.pb.gov.br/servicos/doe/2026/outubro/DIARIO-SINTETICO-NAO-REAL.pdf'
HEAD='GERENCIA EXECUTIVA DE CONCESSAO DE DIREITOS E VANTAGENS\n'
BODY=('RESENHA 1/2026\nDEFERIU PROGRESSAO FUNCIONAL VERTICAL DO GRUPO GAJ\n'
      'SAD-PSE-2026/99991 123456-7 PESSOA SINTETICA UM TECNICO\n')

def record(identifier='sintetico-1'):
    return dict(id=identifier,fonte=URL,data='2026-10-01',resenha='1/2026',
       processo='SAD-PSE-2026/99991',matricula='123456-7',servidor='PESSOA SINTETICA UM',
       pagina=1,eixo='Progressão',modalidade='Vertical',grupo='GAJ',subcategoria='',
       resultado='Deferido',alteracao='Original',validacao='PENDENTE — conferir PDF',
       trecho='FIXTURE SINTETICA, SEM VALOR DOCUMENTAL')

def state():
    return {'edicoes':[{'url':URL,'data':'2026-10-01','arquivo_sha256':'hash-sintetico',
            'status':'PROCESSADO COM PENDÊNCIAS','pendencias':['revisão']}],
            'registros':[record()],'eventos':[]}

def make_pdf(path,texts):
    doc=fitz.open()
    for text in texts:
        p=doc.new_page(width=595,height=842)
        p.insert_textbox(fitz.Rect(30,40,280,800),text,fontsize=8)
    doc.save(path);doc.close()

def local_run(root,pdf,day='2026-10-01',extra=()):
    args=['--pdf',str(pdf),'--data-pdf',day,'--url-pdf',URL,
          '--estado',str(root/'estado.json'),'--saida',str(root/'saida'),*extra]
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        robo.main(args)
    return json.loads((root/'estado.json').read_text())

class SoupFixture:
    """Substituto explícito do parser indisponível; não verifica BeautifulSoup."""
    def __init__(self,html,_parser): self.anchors=json.loads(html)
    def find_all(self,*args,**kwargs):
        class Anchor(dict):
            def get_text(self,*args,**kwargs): return self['title']
        return [Anchor(x) for x in self.anchors]

class Auditoria(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='gediv-auditoria-sintetica-')
        self.root=Path(self.tmp.name);self.pdf=self.root/'SINTETICO.pdf'
        make_pdf(self.pdf,[HEAD+BODY])
    def tearDown(self): self.tmp.cleanup()

    def inventory(self,items):
        def fetch(url,*args):
            # Todas as dez listagens são fixtures; rede e parser são substituídos.
            return json.dumps(items if '/janeiro/' in url or '/outubro/' in url else []).encode()
        with patch.object(robo,'fetch',side_effect=fetch),patch.object(robo,'BeautifulSoup',SoupFixture):
            return robo.discover(date(2026,1,1),date(2026,10,31),None)

    def test_01_limites_inclusivos_inventario(self):
        """Datas-limite: função real de descoberta com rede/parser simulados."""
        items=[{'href':f'https://auniao.pb.gov.br/servicos/doe/diario-oficial-{s}-SINTETICO.pdf',
                'title':'Diario oficial '+s} for s in ['31-12-2025','01-01-2026','31-10-2026','01-11-2026']]
        out=self.inventory(items)
        self.assertEqual([r['data'] for r in out],['2026-01-01','2026-10-31'])

    def test_02_suplemento_documento_distinto(self):
        items=[{'href':f'https://auniao.pb.gov.br/servicos/doe/diario-oficial-01-01-2026-SINTETICO{s}.pdf',
                'title':'Diario oficial 01-01-2026'} for s in ['', '-suplemento']]
        self.assertEqual(len(self.inventory(items)),2)

    def test_03_url_repetida_no_inventario(self):
        a={'href':'https://auniao.pb.gov.br/servicos/doe/diario-oficial-01-01-2026-SINTETICO.pdf',
           'title':'Diario oficial 01-01-2026'}
        self.assertEqual(len(self.inventory([a,a])),1)

    def test_04_pdf_local_exige_data_valida(self):
        with self.assertRaises((ValueError,SystemExit),msg='Data impossível foi aceita pelo modo PDF local'):
            local_run(self.root,self.pdf,'2026-02-30')

    def test_05_pdf_local_respeita_janela_explicita(self):
        out=local_run(self.root,self.pdf,'2026-11-01',
                      ['--inicio','2026-01-01','--fim','2026-10-31'])
        self.assertEqual(len(out['registros']),0,
                         'Modo --pdf aceitou registro posterior à janela informada')

    def test_06_pdf_local_limites_validos(self):
        for day in ['2026-01-01','2026-10-31']:
            with tempfile.TemporaryDirectory() as d:
                out=local_run(Path(d),self.pdf,day)
                self.assertEqual(out['registros'][0]['data'],day)

    def test_07_arquivo_invalido_nao_cria_estado(self):
        self.pdf.write_bytes(b'ARQUIVO SINTETICO QUE NAO E PDF')
        with self.assertRaises(Exception): local_run(self.root,self.pdf)
        self.assertFalse((self.root/'estado.json').exists())

    def test_08_intervalo_invertido_recusado(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            robo.main(['--inicio','2026-10-31','--fim','2026-01-01',
                      '--estado',str(self.root/'x.json')])

    def test_09_limite_zero_recusado(self):
        fake=SimpleNamespace(Session=Mock(return_value=None))
        with patch.object(robo,'requests',fake),patch.object(robo,'discover',return_value=[{'url':URL,'data':'2026-10-01'}]),\
             contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises((ValueError,SystemExit),msg='Lote zero foi aceito como execução normal'):
                robo.main(['--inicio','2026-01-01','--fim','2026-10-31','--max-edicoes','0',
                           '--estado',str(self.root/'estado.json'),'--saida',str(self.root/'saida')])

    def test_10_pdf_nativo_extrai_candidato(self):
        rows,info=robo.pdf_to_records(self.pdf,'2026-10-01',URL)
        self.assertEqual(len(rows),1);self.assertEqual(info['paginas'],1)
        self.assertFalse(robo.reviewed(rows[0]))

    def test_11_tema_sem_gediv_nao_e_incluido(self):
        make_pdf(self.root/'outra.pdf',['SECRETARIA DE OUTRA AREA\n'+BODY])
        rows,_=robo.pdf_to_records(self.root/'outra.pdf','2026-10-01',URL)
        self.assertEqual(rows,[])

    def test_12_continuacao_entre_paginas(self):
        continuation=('CONTINUACAO DA RESENHA 1/2026 PROGRESSAO FUNCIONAL VERTICAL DO GRUPO GAJ\n'
                      'PROCESSO MATRICULA NOME CARGO\n'
                      'SAD-PSE-2026/99992 234567-8 PESSOA SINTETICA DOIS TECNICO\n')
        make_pdf(self.root/'duas.pdf',[HEAD+BODY,continuation])
        rows,info=robo.pdf_to_records(self.root/'duas.pdf','2026-10-01',URL)
        self.assertEqual(len(rows),2,'Continuação sem novo cabeçalho GEDIV foi perdida')

    def test_13_resultado_conflitante_nao_e_inventado(self):
        self.assertEqual(robo.merit('DEFERIDO E INDEFERIDO'),'Não informado')

    def test_14_campos_ausentes_ficam_pendentes(self):
        rows=robo.parse_rows('SAD-PSE-2026/99991 SEM MATRICULA IDENTIFICAVEL',
              '2026-10-01',URL,1,'1/2026','Progressão','Vertical','GAJ','',
              'Não informado','Original','',False)
        self.assertEqual(rows[0]['matricula'],'');self.assertFalse(robo.reviewed(rows[0]))

    def test_15_texto_misto_exige_ocr_por_regiao(self):
        page=Mock(rect=fitz.Rect(0,0,595,842))
        def text(*args,**kw):
            clip=kw.get('clip')
            return HEAD+BODY if clip is None or clip.x0<100 else '\x01\x02\x03'
        page.get_text.side_effect=text
        with patch.object(robo,'ocr_pix',return_value='REGIAO SINTETICA RECUPERADA') as ocr:
            sections=robo.page_sections(page)
        self.assertTrue(ocr.called or any(x[1] for x in sections),
                        'Coluna ilegível foi tratada como texto nativo válido')

    def test_16_variante_documental_abreviada(self):
        value=robo.norm('GERÊNCIA EXECUTIVA DE CONC. DE DIREITOS E VANTAGENS\n'+BODY)
        self.assertEqual(len(list(robo.gediv_blocks(value))),1)

    def test_17_duplicata_exata_deve_ter_alerta(self):
        line='SAD-PSE-2026/99991 123456-7 PESSOA SINTETICA UM TECNICO\n'
        make_pdf(self.root/'dup.pdf',[HEAD+BODY+line])
        rows,info=robo.pdf_to_records(self.root/'dup.pdf','2026-10-01',URL)
        self.assertEqual(len(rows),1)
        self.assertTrue(info['pendencias'],'Colisão eliminada sem alerta de duplicidade')

    def test_18_identidade_ambigua_nao_descarta_pessoa(self):
        line='SAD-PSE-2026/99991 234567-8 PESSOA SINTETICA DOIS TECNICO\n'
        make_pdf(self.root/'colisao.pdf',[HEAD+BODY+line])
        rows,info=robo.pdf_to_records(self.root/'colisao.pdf','2026-10-01',URL)
        self.assertTrue(len(rows)==2 or bool(info['pendencias']),
                        'Mesmo processo, pessoas diferentes: um candidato foi descartado sem alerta')

    def test_19_evento_separado_da_decisao(self):
        make_pdf(self.root/'evento.pdf',[HEAD+'RESENHA 2/2026\nRETIFICACAO DA PUBLICACAO ANTERIOR\n'+BODY.split('\n',1)[1]])
        rows,info=robo.pdf_to_records(self.root/'evento.pdf','2026-10-01',URL)
        self.assertTrue(info['eventos']);self.assertEqual(rows,[])

    def test_20_reexecucao_persistida_nao_duplica(self):
        a=local_run(self.root,self.pdf);b=local_run(self.root,self.pdf)
        self.assertEqual(len(a['registros']),len(b['registros']))
        self.assertEqual(len(b['edicoes']),1)

    def fail_network(self):
        s=state();robo.save_state(s,self.root/'estado.json')
        fake=SimpleNamespace(Session=Mock(return_value=None))
        with patch.object(robo,'requests',fake),patch.object(robo,'discover',return_value=[{'url':URL,'data':'2026-10-01'}]),\
             patch.object(robo,'fetch',side_effect=TimeoutError('FALHA SINTETICA')),\
             contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            value=robo.main(['--inicio','2026-01-01','--fim','2026-10-31',
                   '--estado',str(self.root/'estado.json'),'--saida',str(self.root/'saida')])
        return s,json.loads((self.root/'estado.json').read_text()),value

    def test_21_falha_preserva_registros(self):
        old,new,_=self.fail_network()
        self.assertEqual(old['registros'],new['registros'])
        self.assertGreater(new['cobertura']['ultima_execucao_erros'],0)
        self.assertFalse(robo.completed(new['edicoes'][0]))

    def test_22_falha_total_sinaliza_insucesso_ao_executor(self):
        _,_,exit_code=self.fail_network()
        self.assertEqual(exit_code,2,'CLI precisa retornar código não zero após salvar checkpoint')

    def test_23_checkpoint_corrompido_nao_e_substituido(self):
        p=self.root/'corrompido.json';p.write_text('{INVALIDO')
        before=p.read_bytes()
        with self.assertRaises(ValueError):robo.read_state(p)
        self.assertEqual(p.read_bytes(),before)

    def test_24_pdf_substituido_preserva_versao(self):
        s=state();old=copy.deepcopy(s['registros'])
        meta={'url':URL,'data':'2026-10-01','arquivo_sha256':'nova-versao-sintetica',
              'status':'PROCESSADO','pendencias':[]}
        robo.update(s,meta,[record('novo')],[])
        self.assertEqual(s['historico_versoes'][0]['registros'],old)
        self.assertFalse(robo.completed(s['edicoes'][0]))

    def test_25_checkpoint_interrompido_recuperavel(self):
        p=self.root/'estado.json';robo.save_state(state(),p);before=p.read_bytes()
        with patch.object(Path,'replace',side_effect=OSError('INTERRUPCAO SINTETICA')):
            with self.assertRaises(OSError):robo.save_state({'edicoes':[],'registros':[]},p)
        self.assertEqual(p.read_bytes(),before)
        robo.save_state(state(),p);self.assertEqual(len(robo.read_state(p)['registros']),1)

    def test_26_html_e_dados_coincidem_sem_script_injetado(self):
        s=state();s['registros'][0]['trecho']='</script><script>ERRO_SINTETICO()</script>'
        expected=dashboard.adapt_state(s)
        html=dashboard.build_interactive_html(s,ARGS.source,self.root/'ui').read_text()
        m=re.search(r'window.GEDIV_DATA=(.*?);</script>',html,re.S)
        self.assertEqual(json.loads(m.group(1)),expected)
        self.assertNotIn('</script><script>ERRO_SINTETICO()',html)

    def test_27_pagina_importada_sem_confirmacao_nao_gera_ancora(self):
        a={'records':[{'id':'a','url':URL,'edition':'2026-10-01','page':9,
          'resenha':'1/2026','process':'SAD-PSE-2026/99991','axis':'vertical'}],
          'editions':[{'url':URL,'date':'2026-10-01','pages':12}]}
        s=importar_historico.import_catalog(a)
        self.assertIsNone(dashboard.adapt_state(s)['rows'][0]['page'],
                          'Página de catálogo sem pageConfirmed foi tratada como confirmada')

    def test_28_duplicata_importada_identificada(self):
        a={'id':'a','url':URL,'edition':'2026-10-01','page':1,'process':'SAD-PSE-2026/99991'}
        s=importar_historico.import_catalog({'records':[a,a],'editions':[]})
        flagged=any('duplic' in json.dumps(r,ensure_ascii=False).lower() for r in s['registros'])
        self.assertTrue(len(s['registros'])==1 or flagged,
                        'Dois registros idênticos importados sem sinalização de duplicidade')

    def test_29_validacao_exige_campos_da_decisao(self):
        s=state();s['registros'][0].update(processo='',resultado='Não informado')
        with self.assertRaises(ValueError,msg='Decisão sem processo e resultado recebeu VALIDADO'):
            revisar.review_record(s,'sintetico-1','VALIDADO','REVISOR SINTETICO',
                     'JUSTIFICATIVA SINTETICA PARA TESTE',True)

    def test_30_arquivo_de_saida_tem_permissao_restrita(self):
        p=self.root/'estado.json';robo.save_state(state(),p)
        self.assertEqual(p.stat().st_mode & 0o777,0o600)

    def test_31_workflow_tem_gatilho_manual(self):
        y=(ARGS.source/'.github/workflows/gediv.yml').read_text()
        self.assertIn('workflow_dispatch:',y);self.assertIn('cancel-in-progress: false',y)

    def test_32_agendamento_exige_homologacao(self):
        y=(ARGS.source/'.github/workflows/gediv.yml').read_text()
        if 'schedule:' in y:
            gate=re.search(r'(?i)(homolog\w*|approval|approved)',y)
            self.assertIsNotNone(gate,'Agendamento depende apenas da privacidade do repositório; não há trava de homologação')

    def test_33_retomada_apos_falha_de_rede(self):
        _,failed,_=self.fail_network()
        self.assertFalse(robo.completed(failed['edicoes'][0]))
        fake=SimpleNamespace(Session=Mock(return_value=None))
        with patch.object(robo,'requests',fake),patch.object(robo,'discover',return_value=[{'url':URL,'data':'2026-10-01'}]),\
             patch.object(robo,'fetch',return_value=self.pdf.read_bytes()),\
             contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            robo.main(['--inicio','2026-01-01','--fim','2026-10-31',
               '--estado',str(self.root/'estado.json'),'--saida',str(self.root/'saida')])
        resumed=robo.read_state(self.root/'estado.json')
        self.assertEqual(resumed['cobertura']['ultima_execucao_erros'],0)
        self.assertEqual(len(resumed['registros']),1)
        self.assertFalse(robo.reviewed(resumed['registros'][0]))

