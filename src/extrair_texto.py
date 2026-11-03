#!/usr/bin/env python3
"""Ponte manual rastreável: texto oficial por página -> lote privado do painel.

Aceita texto nativo já obtido do PDF ou recorte indexado. Texto indexado nunca
comprova cobertura integral nem substitui o SHA do PDF. Não lê/escreve banco.
"""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
import dashboard
import robo


def extract(packet, nature='real', start='2026-01-01', end='2026-10-31'):
    url=packet['url']; day=packet['data']
    parsed=date.fromisoformat(day)
    if not date.fromisoformat(start)<=parsed<=date.fromisoformat(end):
        raise ValueError('Edição fora da janela de publicação')
    if not robo.official_url(url) or not url.split('?')[0].lower().endswith('.pdf'):
        raise ValueError('Informe a referência PDF do acervo oficial')
    method=packet.get('metodo')
    if method not in {'texto_indexado','texto_nativo_pdf'}:
        raise ValueError('Método de obtenção não informado')
    if nature not in {'real','sintetico'}: raise ValueError('Natureza inválida')
    if not packet.get('referencia'): raise ValueError('Referência de obtenção obrigatória')
    pages=packet.get('paginas')
    if not pages or not isinstance(pages,list): raise ValueError('Páginas ausentes')
    rows=[]; events=[]; issues=[]; page_ids=[]
    digest=hashlib.sha256(json.dumps(pages,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    for page in pages:
        number=page['pagina']; raw=page['texto']
        if type(number) is not int or number<1 or number in page_ids or not isinstance(raw,str):
            raise ValueError('Página inválida ou repetida')
        page_ids.append(number)
        if number>packet.get('paginas_totais',number): raise ValueError('Página supera total declarado')
        blocks=list(robo.gediv_blocks(robo.norm(raw)))
        for block in blocks:
            # Uma publicação termina em PUBLIQUE-SE. Não atribuir à GEDIV
            # atos de outras unidades colocados abaixo do fechamento.
            block=re.split(r'(?m)^\s*PUBLIQUE-SE\b',block,maxsplit=1)[0]
            matches=list(robo.PAT_RES.finditer(block))
            if not matches:
                issues.append(f'p.{number}: bloco GEDIV sem resenha; conferir'); continue
            for i,match in enumerate(matches):
                act=block[match.start():matches[i+1].start() if i+1<len(matches) else len(block)]
                rid=match.group(1); kind=robo.alteration(act)
                if kind!='Original':
                    event_id=hashlib.sha256(f'{url}|{number}|{rid}|{act}'.encode()).hexdigest()[:20]
                    events.append({'id':event_id,'data':day,'fonte':url,'pagina':number,
                                   'resenha_modificadora':rid,'tipo':kind,
                                   'trecho':robo.compact(act)[:1000],'validacao':'PENDENTE_VINCULACAO'})
                    continue
                axis,mod,group,sub=robo.hierarchy(act)
                if axis=='Outras publicações GEDIV':
                    issues.append(f'p.{number} resenha {rid}: tema fora dos dois eixos'); continue
                first=robo.PAT_PROC.search(act)
                result=robo.merit(act[:first.start()] if first else act)
                found=robo.parse_rows(act,day,url,number,rid,axis,mod,group,sub,result,kind,'expresso',False)
                for row in found:
                    row['extracao']='Texto indexado — recorte' if method=='texto_indexado' else 'Texto nativo do PDF'
                    row['conferencia_previa']='Extração automática rastreável; conteúdo e vínculo ainda exigem revisão humana.'
                    row['pagina_confirmada_origem']=packet.get('pagina_visual_conferida') is True
                    row['texto_sha256']=digest
                rows.extend(found)
    unique={}
    for row in rows:
        if row['id'] in unique: issues.append('Ocorrência repetida no texto de origem; conferir duplicidade')
        else: unique[row['id']]=row
    rows=list(unique.values())
    issues+=['Cobertura parcial: recorte por página; não comprova leitura integral da edição.',
             'Revisão humana do PDF e dos campos obrigatórios pendente.']
    meta={'url':url,'data':day,'paginas':packet.get('paginas_totais'),
          'paginas_lidas':sorted(page_ids),'status':'PROCESSADO COM PENDÊNCIAS',
          'registros':len(rows),'pendencias':issues,'texto_sha256':digest}
    if packet.get('arquivo_sha256'): meta['arquivo_sha256']=packet['arquivo_sha256']
    state={'edicoes':[meta],'registros':rows,'eventos':events,'atualizado_em':robo.now()}
    provenance={'url':url,'date':day,'method':method,'reference':packet['referencia'],
                'textSha256':digest,'pdfSha256':packet.get('arquivo_sha256'),
                'pagesRead':sorted(page_ids),'pagesTotal':packet.get('paginas_totais'),
                'coverage':'partial','issues':issues}
    return state,{'schemaVersion':1,'nature':nature,'data':dashboard.adapt_state(state),
                  'provenance':provenance}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--entrada',required=True,type=Path)
    p.add_argument('--saida',required=True,type=Path,help='Diretório NOVO de saída privada')
    p.add_argument('--natureza',required=True,choices=['real','sintetico'])
    p.add_argument('--inicio',default='2026-01-01');p.add_argument('--fim',default='2026-10-31')
    a=p.parse_args(argv)
    state,batch=extract(json.loads(a.entrada.read_text()),a.natureza,a.inicio,a.fim)
    a.saida.mkdir(mode=0o700,parents=True,exist_ok=False)
    robo.write_private(a.saida/'estado_novo.json',json.dumps(state,ensure_ascii=False,indent=2))
    robo.write_private(a.saida/'lote.json',json.dumps(batch,ensure_ascii=False,separators=(',',':')))
    print(json.dumps({'registros':len(state['registros']),'eventos':len(state['eventos']),
                      'metodo':batch['provenance']['method'],'cobertura':'parcial','validados':0}))
if __name__=='__main__':main()
