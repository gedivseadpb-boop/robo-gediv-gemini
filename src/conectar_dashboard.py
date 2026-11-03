#!/usr/bin/env python3
"""Entrega manual de lote real ao painel privado, com recibo idempotente.

Usa somente o token de serviço do MESMO Site, recebido por variável de ambiente.
Não imprime credenciais nem as grava em arquivos. Nunca segue redirecionamentos.
"""
import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

SITE='https://gediv-conferencia-privada-20261031.ylenaluna.chatgpt.site'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def deliver(batch,token):
    if not token: raise ValueError('Acesso de serviço ao Site não configurado')
    if batch.get('schemaVersion')!=1 or batch.get('nature')!='real':
        raise ValueError('Somente lote real com contrato versão 1')
    data=json.dumps(batch,ensure_ascii=False,separators=(',',':')).encode()
    if len(data)>5_000_000: raise ValueError('Lote excede 5 MB')
    request=urllib.request.Request(SITE+'/api/ingest',data=data,method='POST',headers={
        'Content-Type':'application/json','OAI-Sites-Authorization':'Bearer '+token})
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=30) as response:
            receipt=json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Entrega não confirmada: HTTP {exc.code}. Conserve o lote para reenvio.') from None
    except urllib.error.URLError:
        raise RuntimeError('Entrega não confirmada: falha de rede. Conserve o lote para reenvio.') from None
    if receipt.get('status') not in {'recebido','ja_recebido'} or not receipt.get('batchId'):
        raise RuntimeError('Recibo inválido; não declarar entrega concluída')
    return receipt

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lote',required=True,type=Path)
    args=parser.parse_args(argv)
    batch=json.loads(args.lote.read_text())
    receipt=deliver(batch,os.getenv('GEDIV_SITES_TOKEN',''))
    print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
