#!/usr/bin/env python3
"""Coletor conservador GEDIV: DOE-PB -> PDF -> registros auditáveis -> HTML.
Requer internet APENAS durante collect. PDFs locais funcionam sem rede.
"""
import argparse, copy, hashlib, json, os, re, sys, time, unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo
import fitz
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests=None
    BeautifulSoup=None

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://auniao.pb.gov.br"
MESES = ["","janeiro","fevereiro","marco","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
PAT_DATA = re.compile(r"(?<!\d)(\d{2})[-_/](\d{2})[-_/](20\d{2})(?!\d)")
PAT_PROC = re.compile(r"(?:SAD[\s-]*PSE[\s-]*\d{4}/\d{4,8}|[A-Z]{2,6}[\s-]*(?:PRC|PSE)[\s-]*\d{4}/\d{3,9})",re.I)
PAT_RES = re.compile(r"\bRESENHA\s*(?:N[Oº°.]*)?\s*:?\s*(\d{1,5}/20\d{2})",re.I)
PAT_GEDIV = re.compile(r"GERENCIA\s+EXECUTIVA\s+(?:DE\s+)?(?:CONC\.?\s*(?:DE\s+)?|CONCESSAO\s+DE\s+)?DIREITOS\s+E\s+VANTAGENS", re.I)
PAT_OTHER_GERENCIA = re.compile(r"GERENCIA\s+EXECUTIVA\s+(?!.*DIREITOS\s+E\s+VANTAGENS)",re.I)
REG = re.compile(r"\b\d{5,7}[-]?\d\b")
TYPES = [
 ("Anotação de Tempo",r"ANOTACAO\s+(?:DE\s+)?TEMPO"),
 ("Desaverbação",r"DESAVERBACAO"),
 # Casos específicos antes dos termos genéricos: evita confundir conversão
 # em tempo de serviço com licença especial original e desistência com licença.
 ("Desistência de Licença",r"DESISTENCIA\s+DE\s+LICENCA"),
 ("Conversão de Licença Especial",r"CONVERSAO\s+DE\s+LICENCA\s+ESPECIAL"),
 ("Conversão de Férias",r"CONVERSAO\s+DE\s+FERIAS"),
 ("Licença para Interesses Particulares",r"LICENCA\s+PARA\s+(?:TRATO|TRATAR)\s+DE\s+INTERESSES?\s+PARTICULARES|LICENCA\s+(?:PARA\s+)?TRATO\s+DE"),
 ("Licença Especial",r"LICENCA\s+ESPECIAL"),
]
GROUPS = [
("MAG",r"\bMAG\b|MAGISTERIO|EDUCACAO\s+BASICA"),
("SAÚDE",r"GRUPO\s+SAUDE|PROFISSIONAIS\s+DO\s+GRUPO\s+SAUDE"),
("GAJ",r"\bGAJ(?:-\d{3,4})?\b|APOIO\s+JUDICIARIO"),
("FAP",r"\bFAP(?:-\d{3,4})?\b|FISCALIZACAO\s+AGROPECUARIA"),
("ANS",r"\bANS(?:-\d{3,4})?\b|OUTRAS\s+ATIVIDADES\s+DE\s+NIVEL\s+SUPERIOR"),
("AST",r"\bAST\b|TECNICOS?\s+ADMINISTRATIVOS?|TEC\.\s*ADM"),
("DPS",r"\bDPS(?:-\d{3,4})?\b|DIVULGACAO\s+E\s+PROMOCAO"),
("PPGG",r"\bPPGG(?:-\d{3,4})?\b|POLITICAS\s+PUBLICAS\s+E\s+GESTAO"),
("FAP",r"FISCAL\s+ESTADUAL\s+AGROPECUARIO"),
("ESPECIAL",r"GRUPO\s+(?:OCUPACIONAL\s+)?ESPECIAL"),
("SFT",r"\bSFT\b|SERVIDORES\s+FISCAIS\s+TRIBUTARIOS"),
]
JOBS = r"(?:TECNIC[OA]|T[EÉ]CNIC[OA]|ATENDENTE|BIOQUIMIC[OA]|FONOAUDIOLOG[OA]|PROFESSOR[A]?|FISCAL|ENFERMEIR[OA]|FARMACEUTIC[OA]|AUXILIAR|AUDITOR[A]?|POLICIAL|AGENTE|ANALISTA|FISIOTERAPEUTA)"
def norm(s):
    return "".join(c for c in unicodedata.normalize("NFKD",str(s)) if not unicodedata.combining(c)).upper()
def compact(s):
    return re.sub(r"\s+"," ",s or "").strip()
def now():
    return datetime.now(ZoneInfo("America/Fortaleza")).isoformat(timespec="seconds")

def official_url(url):
    """Só aceita o acervo HTTPS oficial, sem credenciais nem domínios parecidos."""
    try:
        parsed=urlsplit(url)
        return (parsed.scheme.lower()=="https" and
                parsed.hostname in {"auniao.pb.gov.br", "www.auniao.pb.gov.br"} and
                parsed.username is None and parsed.password is None and
                parsed.port in (None,443))
    except ValueError:
        return False

def completed(meta):
    """Parcial ou com pendências nunca equivale a processamento completo."""
    return bool(meta) and meta.get("status")=="PROCESSADO" and not meta.get("pendencias")

def reviewed(row):
    return norm(row.get("validacao", "")).strip() in {"VALIDADO","VALIDADA","CONFERIDO","CONFERIDA"}

def rejected(row):
    return norm(row.get("validacao", "")).strip() in {"REJEITADO","REJEITADA","EXCLUIDO","EXCLUIDA"}

def write_private(path,content):
    """Cria o arquivo já restrito, sem janela inicial de leitura pública."""
    flags=os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,"O_NOFOLLOW",0)
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as stream:
        if hasattr(os,"fchmod"): os.fchmod(stream.fileno(),0o600)
        stream.write(content)

def fetch(url,session,max_bytes=25_000_000):
    if not official_url(url):
        raise ValueError("URL fora do domínio oficial do DOE")
    for attempt in range(3):
        try:
            current=url
            for _ in range(6):
                r=session.get(current,timeout=(15,60),headers={"User-Agent":"GEDIV-Monitor/1.0 (consulta pública; contato pelo repositório)"},stream=True,allow_redirects=False)
                try:
                    if r.status_code in (301,302,303,307,308):
                        location=r.headers.get("Location")
                        target=urljoin(current,location or "")
                        if not location or not official_url(target):
                            raise ValueError("Redirecionamento fora da fonte oficial")
                        current=target
                        continue
                    r.raise_for_status()
                    data=bytearray()
                    for part in r.iter_content(65536):
                        data.extend(part)
                        if len(data)>max_bytes: raise ValueError("Arquivo excede o tamanho permitido")
                    return bytes(data)
                finally:
                    r.close()
            raise ValueError("Limite de redirecionamentos excedido")
        except (requests.RequestException,ValueError):
            if attempt==2: raise
            time.sleep(2*(attempt+1))
def discover(start,end,session):
    urls={}
    cursor=date(start.year,start.month,1)
    while cursor<=end:
        month= f"{BASE_URL}/servicos/doe/{cursor.year}/{MESES[cursor.month]}/"
        for page in range(20):  # portal usa ?b_start:int=20
            url=month if page==0 else month+"?b_start:int="+str(page*20)
            html=fetch(url,session,5_000_000).decode("utf-8","replace")
            anchors=BeautifulSoup(html,"html.parser").find_all("a",href=True)
            found=0
            for a in anchors:
                href=urljoin(url,a["href"])
                title=(a.get_text(" ",strip=True)+" "+href)
                if not re.search(r"diario.oficial",norm(title),re.I): continue
                m=PAT_DATA.search(title)
                if not m: continue
                try: dt=date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
                except ValueError: continue
                found+=1
                if not start<=dt<=end: continue
                if "/view" in href: href=href.split("/view")[0]
                href=href.split("?")[0]
                if not href.lower().endswith(".pdf"): continue
                if not official_url(href): continue
                urls[href]=dt.isoformat()
            if not found or not any("b_start" in a["href"] for a in anchors): break
        cursor=date(cursor.year+(cursor.month==12),cursor.month%12+1,1)
    return sorted(({"url":u,"data":d} for u,d in urls.items()),key=lambda x:(x["data"],x["url"]))

def text_quality(t):
    if not t.strip(): return False
    bad=sum(ord(ch)<32 and ch not in "\n\r\t" for ch in t)
    return (bad/max(len(t),1)<.025
            and len(re.findall(r"[A-Za-zÀ-ÿ]{3,}",t))>=10
            and bool(re.search(r"SECRETARIA|DIARIO|RESENHA|PARA[IÍ]BA|GOVERNO|GER[EÊ]NCIA|PORTARIA",norm(t))))

def ocr_pix(page,clip=None,scale=3.4,psm=6):
    from PIL import Image
    import pytesseract
    p=page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip,alpha=False)
    image=Image.frombytes("RGB",(p.width,p.height),p.samples)
    return pytesseract.image_to_string(image,lang="por",config=f"--psm {psm}")

def page_sections(page):
    """Avalia cada coluna: texto legível em uma não encobre a outra."""
    r=page.rect
    mid=(r.x0+r.x1)/2
    cols=[fitz.Rect(r.x0,r.y0,mid+8,r.y1),fitz.Rect(mid-8,r.y0,r.x1,r.y1)]
    sections=[]
    for index,col in enumerate(cols,1):
        raw=page.get_text("text",clip=col,sort=True)
        if text_quality(raw):
            sections.append((raw,False))
            continue
        # Coluna vazia em PDF nativo pode estar em branco. Imagens e texto
        # cifrado exigem OCR; em falha, conservar as outras regiões e alertar.
        if not raw.strip() and not page.get_images():
            sections.append(("",False)); continue
        try:
            sections.append((ocr_pix(page,clip=col,scale=2.5,psm=6),True))
        except Exception as exc:
            sections.append((f"[FALHA_OCR_COLUNA_{index}: {type(exc).__name__}]\n"+raw,True))
    return sections

def hierarchy(text):
    t=norm(text)
    eixo="Não classificado"; modalidade=""; grupo=""; subcat=""
    if "PROGRESSAO" in t:
        eixo="Progressão"
        if "HORIZONTAL" in t: modalidade="Horizontal"
        elif "VERTICAL" in t: modalidade="Vertical"
        for code,pat in GROUPS:
            if re.search(pat,t): grupo=code; break
    else:
        for label,pat in TYPES:
            if re.search(pat,t):
                eixo="Tempo de Serviço"; subcat=label; break
    if eixo=="Não classificado": eixo="Outras publicações GEDIV"
    return eixo,modalidade,grupo,subcat


def merit(text):
    t=norm(text)
    matches=set(re.findall(r"\b(INDEFERI(?:U|R|DO|DOS|DA|DAS|MOS)|DEFERI(?:U|R|DO|DOS|DA|DAS|MOS))\b",t))
    yes=any(x.startswith("DEFERI") for x in matches)
    no=any(x.startswith("INDEFERI") for x in matches)
    if yes and no: return "Não informado"
    if no: return "Indeferido"
    if yes: return "Deferido"
    return "Não informado"

def alteration(text):
    t=norm(text)
    if re.search(r"TORNAD[OA]?\s+SEM\s+EFEITO|TORNAR\s+SEM\s+EFEITO",t): return "Sem efeito"
    if re.search(r"REPUBLICA|REPUBLICAD|RETIFIC|CORRIG|ONDE\s+SE\s+LE",t): return "Refeito (vínculo pendente)"
    return "Original"

def gediv_blocks(text):
    """Isola cada cabeçalho GEDIV sem atravessar outra unidade na mesma coluna."""
    heads=list(PAT_GEDIV.finditer(text))
    starts=[]
    for i,head in enumerate(heads):
        start=head.start()
        # Algumas edições imprimem o número antes da identificação da unidade.
        # Não transportar a resenha anterior após processo ou decisão já vistos.
        previous_end=heads[i-1].end() if i else max(0,start-700)
        previous=list(PAT_RES.finditer(text[previous_end:start]))
        if previous:
            res=previous[-1]
            absolute=previous_end+res.start()
            between=text[previous_end+res.end():start]
            if (start-absolute<700 and not PAT_PROC.search(between) and
                    not PAT_OTHER_GERENCIA.search(between) and
                    not re.search(r"\b(?:IN)?DEFERI(?:U|R|DO|DOS|DA|DAS|MOS)\b",between)):
                start=absolute
        starts.append(start)
    for i,head in enumerate(heads):
        start=starts[i]
        end=starts[i+1] if i+1<len(heads) else len(text)
        boundary=re.search(r"(?m)^[ \t]*(?:SECRETARIA[ \t]+DE[ \t]+ESTADO\b|GERENCIA[ \t]+EXECUTIVA\b)",
                           text[head.end():end])
        if boundary: end=head.end()+boundary.start()
        yield text[start:end]

def parse_rows(text,dt,url,page_no,resenha,eixo,modalidade,grupo,subcat,resultado,alteracao,origin,ocr):
    matches=list(PAT_PROC.finditer(text))
    rows=[]
    if not matches: return rows
    for i,m in enumerate(matches):
        span=text[m.end():(matches[i+1].start() if i+1<len(matches) else m.end()+230)]
        flat=compact(span)
        reg=REG.search(flat)
        matricula=reg.group() if reg else ""
        name=""
        if reg:
            rest=flat[reg.end():].strip()
            # Nome geralmente precede o cargo, mas não inventar se não identificável.
            job=re.search(r"\b"+JOBS+r"\b",rest,re.I)
            if job: name=compact(rest[:job.start()]).strip(" |-")
            else:
                # Tabelas de tempo não têm cargo. Parecer e colunas numéricas
                # delimitam o nome; conservar a transcrição como candidato.
                rest=re.split(r"\s+(?:(?:PBPREV|PARECER)\b|\d)",rest,maxsplit=1)[0]
                nm=re.match(r"([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÇ .'-]{5,75})",rest)
                if nm: name=nm.group(1).strip()
        if len(name)>90: name=""
        proc=compact(m.group()).replace(" ","").upper()
        row_result=merit(span)
        has_result=bool(re.search(r"\b(?:IN)?DEFERI(?:U|R|DO|DOS|DA|DAS|MOS)\b",norm(span)))
        effective=row_result if has_result else resultado
        unique=hashlib.sha256(f"{url}|{page_no}|{resenha}|{proc}|{matricula}|{name}|{effective}|{eixo}|{modalidade}|{subcat}".encode()).hexdigest()[:20]
        rows.append({"id":unique,"data":dt,"resenha":resenha or "",
          "processo":proc,"servidor":name,"matricula":matricula,
          "eixo":eixo,"modalidade":modalidade,"grupo":grupo,"subcategoria":subcat,
          "resultado":effective,"alteracao":alteracao,"pagina":page_no,
          "fonte":url,"extracao":"OCR" if ocr else "Texto",
          "validacao":"PENDENTE — conferir PDF","pagina_confirmada_origem":True,
          "mencao_gediv_origem":"expresso" if origin!="continuidade" else "continuidade_a_conferir",
          "trecho":compact(text[max(0,m.start()-70):m.end()+220])[:320]})
    return rows

def pdf_to_records(pdf,dt,url):
    rows=[]; events=[]; issues=[]; page_count=0; resenhas=set()
    continuation=None
    with fitz.open(pdf) as document:
        page_count=len(document)
        for pno,page in enumerate(document,1):
            try:
                sections=page_sections(page)
                if any(ocr for _,ocr in sections):
                    issues.append(f"p.{pno}: OCR requer conferência da página e das colunas.")
                for raw,ocr in sections:
                    text=norm(raw)
                    candidates=list(gediv_blocks(text))
                    inherited=False
                    # Só herdar contexto com marcador explícito e a MESMA resenha.
                    # Tabelas soltas e atos de outra unidade não provam GEDIV.
                    if not candidates and continuation and re.search(r"CONTINUA",text):
                        match=PAT_RES.search(text)
                        if match and match.group(1)==continuation['resenha'] and not PAT_OTHER_GERENCIA.search(text):
                            candidates=[text]; inherited=True
                            issues.append(f"p.{pno}: continuação da resenha {match.group(1)} exige conferência de vínculo.")
                    for candidate in candidates:
                        rm=list(PAT_RES.finditer(candidate))
                        if not rm:
                            issues.append(f"p.{pno}: GEDIV identificada sem resenha numerada; revisar ato individual.")
                        acts=[]
                        if rm:
                            for j,m in enumerate(rm):
                                end=rm[j+1].start() if j+1<len(rm) else len(candidate)
                                acts.append((m.group(1),candidate[m.start():end]))
                        else: acts=[("",candidate)]
                        for rid,act in acts:
                            eixo,mod,grupo,sub=hierarchy(act)
                            if inherited:
                                eixo,mod,grupo,sub=continuation['hierarquia']
                            alt=alteration(act)
                            if alt!="Original":
                                event_id=hashlib.sha256(f"{url}|{pno}|{rid}|{alt}|{act}".encode()).hexdigest()[:20]
                                events.append({"id":event_id,"data":dt,"fonte":url,"pagina":pno,
                                    "resenha_modificadora":rid,"tipo":alt,"validacao":"PENDENTE_VINCULACAO",
                                    "trecho":compact(act)[:1000]})
                                continue
                            first_proc=PAT_PROC.search(act)
                            result=merit(act[:first_proc.start()] if first_proc else act)
                            if inherited and result=='Não informado': result=continuation['resultado']
                            if eixo=="Outras publicações GEDIV":
                                issues.append(f"p.{pno} resenha {rid or '?'}: tema fora dos dois eixos; revisar.")
                            recs=parse_rows(act,dt,url,pno,rid,eixo,mod,grupo,sub,result,alt,"continuidade" if inherited else "expresso",ocr)
                            if not recs:
                                # OCR de página inteira pode pertencer a outra unidade; não atribuí-lo ao bloco.
                                issues.append(f"p.{pno} resenha {rid or '?'}: sem processos extraídos no bloco; exige revisão.")
                            else:
                                rows+=recs
                                resenhas.add((dt,rid))
                                continuation={'resenha':rid,'hierarquia':(eixo,mod,grupo,sub),'resultado':result}
                    if not candidates and (PAT_OTHER_GERENCIA.search(text) or re.search(r"SECRETARIA\s+DE\s+ESTADO",text)):
                        continuation=None
            except Exception as exc:
                issues.append(f"p.{pno}: falha de leitura {str(exc)[:120]}")
    # deduplicação mantendo alerta, nunca inventar valores em colisão
    clean={}
    for row in rows:
        if row['id'] in clean:
            issues.append(f"p.{row['pagina']}: ocorrência repetida na resenha {row['resenha']}; conferir duplicidade.")
        else: clean[row['id']]=row
    unique_events={e["id"]:e for e in events}
    return list(clean.values()), {"paginas":page_count,"resenhas":len(resenhas),"pendencias":issues,"eventos":list(unique_events.values())}

def read_state(path):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: raise ValueError("Estado JSON inválido; faça backup antes de continuar")
    return {"edicoes":[],"registros":[],"eventos":[],"historico_versoes":[],"atualizado_em":None}
def save_state(state,path):
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    state["atualizado_em"]=now()
    temp=path.with_suffix(".tmp")
    write_private(temp,json.dumps(state,ensure_ascii=False,indent=2))
    temp.replace(path)
def update(state,meta,rows,events=None):
    meta=copy.deepcopy(meta)
    previous=next((x for x in state["edicoes"] if x.get("url")==meta["url"]),None)
    old_rows=[r for r in state["registros"] if r.get("fonte")==meta["url"]]
    old_events=[e for e in state.get("eventos",[]) if e.get("fonte")==meta["url"]]
    old_hash=previous.get("arquivo_sha256") if previous else None
    new_hash=meta.get("arquivo_sha256")
    changed=bool(old_hash and new_hash and old_hash!=new_hash)
    if changed:
        # Guardar o resultado e as evidências anteriores antes de trocar o PDF.
        snapshots=state.setdefault("historico_versoes",[])
        if not any(x.get("url")==meta["url"] and x.get("arquivo_sha256")==old_hash for x in snapshots):
            snapshots.append({"url":meta["url"],"arquivo_sha256":old_hash,
                "edicao":copy.deepcopy(previous),"registros":copy.deepcopy(old_rows),
                "eventos":copy.deepcopy(old_events),"arquivada_em":now()})
        meta["versao_alterada_pendente"]=True
    elif previous and previous.get("versao_alterada_pendente"):
        meta["versao_alterada_pendente"]=True
    if meta.get("versao_alterada_pendente"):
        issues=meta.setdefault("pendencias",[])
        message="PDF alterado: conferir versão anterior antes de validar a edição."
        if message not in issues: issues.append(message)
        meta["status"]="PROCESSADO COM PENDÊNCIAS"
    # Para o mesmo PDF, conservar candidatos anteriores e revisões humanas.
    if old_hash and new_hash==old_hash:
        merged={r["id"]:r for r in old_rows}
        for row in rows:
            prior=merged.get(row["id"])
            if prior is None or (not reviewed(prior) and not rejected(prior)):
                merged[row["id"]]=row
        rows=list(merged.values())
        if events is not None:
            merged_events={e["id"]:e for e in old_events}
            for event in events:
                prior=merged_events.get(event["id"])
                if prior is None or (not reviewed(prior) and not rejected(prior)):
                    merged_events[event["id"]]=event
            events=list(merged_events.values())
    meta["registros"]=len(rows)
    by_url={x["url"]:x for x in state["edicoes"]}
    by_url[meta["url"]]=meta
    state["edicoes"]=list(by_url.values())
    # As versões de PDF alterado permanecem em historico_versoes.
    kept=[r for r in state["registros"] if r.get("fonte")!=meta["url"]]
    by_id={r["id"]:r for r in kept}
    for r in rows:
        by_id[r["id"]]=r
    state["registros"]=sorted(
        by_id.values(),key=lambda x:(x["data"],x["resenha"],x["processo"]),reverse=True)
    if events is not None:
        state["eventos"]=[e for e in state.get("eventos",[]) if e.get("fonte")!=meta["url"]]+events

def build_html(state,outdir):
    template=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
    outdir.mkdir(mode=0o700,parents=True,exist_ok=True)
    def write(filename,data):
        # substituição segura para tag JSON
        embedded=json.dumps(data,ensure_ascii=False).replace("<","\\u003c").replace("</","<\\/")
        target=outdir/filename
        write_private(target,template.replace("__GEDIV_EMBED_DATA__",embedded))
    repo=os.getenv("GITHUB_REPOSITORY","")
    workflow_url=f"https://github.com/{repo}/actions/workflows/gediv.yml" if repo else ""
    write("painel_privado.html",{"mode":"privado","workflow_url":workflow_url,**state})
    # Não gerar uma cópia pública com linhas individuais.
    aggregate=outdir/"dados_agregados.json"
    write_private(aggregate,json.dumps({"atualizado_em":state.get("atualizado_em"),"edicoes":len(state["edicoes"]),"decisoes_validadas":sum(reviewed(r) for r in state["registros"]),"candidatos_pendentes":sum(not reviewed(r) and not rejected(r) for r in state["registros"])},ensure_ascii=False))
    from dashboard import build_interactive_html
    build_interactive_html(state,ROOT,outdir,workflow_url)
def main(argv=None):
    ap=argparse.ArgumentParser(description="Robô GEDIV — DOE Paraíba")
    ap.add_argument("--inicio",default=None)
    ap.add_argument("--fim",default=None)
    ap.add_argument("--pdf",help="Teste local: caminho PDF existente, sem acesso à internet")
    ap.add_argument("--data-pdf",help="Data oficial do PDF local: AAAA-MM-DD")
    ap.add_argument("--url-pdf",default="",help="Fonte oficial comprovada; deixe em branco se documento enviado")
    ap.add_argument("--estado",default=str(ROOT/"storage"/"estado.json"))
    ap.add_argument("--saida",default=str(ROOT/"output"))
    ap.add_argument("--max-edicoes",type=int,default=12,
                    help="Quantidade MÁXIMA de edições a conferir nesta execução; repetir para continuar histórico")
    ap.add_argument("--modo",choices=["historico","diario","periodo"],default="diario",
                    help="historico: antigas pendentes primeiro; diario: recentes primeiro + backlog; periodo: ordem cronológica")
    ap.add_argument("--rever-dias",type=int,default=14,
                    help="Conferir se PDFs recentes foram substituídos (modo diário)")
    args=ap.parse_args(argv)
    if args.max_edicoes < 1: ap.error("--max-edicoes precisa ser positivo")
    try:
        local_day=date.fromisoformat(args.data_pdf) if args.data_pdf else None
        end=date.fromisoformat(args.fim) if args.fim else (local_day or date.today())
        start=date.fromisoformat(args.inicio) if args.inicio else (local_day or end-timedelta(days=14))
    except ValueError:
        ap.error("Data inválida; informe AAAA-MM-DD")
    if end<start: ap.error("Intervalo inválido")
    statefile=Path(args.estado); state=read_state(statefile)
    total_errors=0
    if args.pdf:
        if not args.data_pdf: ap.error("--data-pdf é obrigatório com --pdf")
        if not start<=local_day<=end:
            print("PDF fora do período solicitado; nenhum registro incluído.")
            save_state(state,statefile)
            build_html(state,Path(args.saida))
            return 0
        pdf=Path(args.pdf)
        if not pdf.is_file(): ap.error("PDF não encontrado: "+str(pdf))
        url=args.url_pdf or "Documento fornecido para teste local — referência oficial não comprovada"
        rows,info=pdf_to_records(pdf,args.data_pdf,url)
        meta={"url":url,"data":args.data_pdf,"arquivo_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),"status":"PROCESSADO COM PENDÊNCIAS" if info["pendencias"] else "PROCESSADO","paginas":info["paginas"],"registros":len(rows),"pendencias":info["pendencias"]}
        update(state,meta,rows,info["eventos"])
        print("PDF local",json.dumps(meta,ensure_ascii=False),len(rows),"registros")
    else:
        session=requests.Session()
        editions=discover(start,end,session)
        print(f"Localizadas {len(editions)} edições na fonte oficial para {start} a {end}",flush=True)
        if not editions:
            # Não confundir falha de descoberta com ausência de publicações.
            raise RuntimeError("Nenhuma edição descoberta. Verifique o portal, as datas e o HTML.")
        cache=ROOT/"cache"; cache.mkdir(exist_ok=True)
        previous={e["url"]:e for e in state["edicoes"]}
        threshold=(end-timedelta(days=max(args.rever_dias,0))).isoformat()
        pending=[e for e in editions
                 if e["url"] not in previous
                 or not completed(previous[e["url"]])]
        recent=[e for e in editions if e["data"]>=threshold]
        if args.modo=="diario":
            # Conservar parte do lote para histórico, mesmo que haja muitas
            # edições recentes a conferir. Revisar as mais novas e alternar
            # o grupo de rechecagem dos últimos 14 dias ao longo da semana.
            recent.sort(key=lambda e:(e["data"],e["url"]),reverse=True)
            newest_n=min(3,max(1,args.max_edicoes//4))
            other_n=min(3,max(0,args.max_edicoes//4))
            newest=recent[:newest_n]
            older_recent=recent[newest_n:]
            rotated=[]
            if older_recent:
                ix=(end.toordinal()*max(other_n,1)) % len(older_recent)
                extended=older_recent[ix:]+older_recent[:ix]
                rotated=extended[:other_n]
            priority=newest+rotated
            candidates=priority+[e for e in pending if e not in priority]+[
                e for e in recent if e not in priority]
        elif args.modo=="historico":
            candidates=pending
        else:
            candidates=sorted({e["url"]:e for e in (pending+recent)}.values(),
                              key=lambda e:(e["data"],e["url"]))
        # URLs únicas e quantidade de trabalho limitada. Reexecuções retomam
        # do estado.json, mantido no repositório PRIVADO.
        todo=list({e["url"]:e for e in candidates}.values())[:args.max_edicoes]
        print(f"Edições pendentes = {len(pending)} | agendadas neste lote = {len(todo)}",flush=True)
        total_errors=0
        for entry in todo:
            url=entry["url"]; dt=entry["data"]
            meta={"url":url,"data":dt,"paginas":0,"registros":0,"status":"ERRO","pendencias":[]}
            try:
                binary=fetch(url,session)
                if binary[:4]!=b"%PDF":
                    raise ValueError("Servidor retornou conteúdo que não é PDF")
                sha=hashlib.sha256(binary).hexdigest()
                meta["arquivo_sha256"]=sha
                existing=previous.get(url)
                if (existing and existing.get("arquivo_sha256")==sha
                    and completed(existing)):
                    print("Sem alterações",dt,url,flush=True)
                    continue
                name=cache/(sha[:20]+".pdf");name.write_bytes(binary)
                records,info=pdf_to_records(name,dt,url)
                meta.update({"paginas":info["paginas"],"registros":len(records),
                    "pendencias":info["pendencias"],
                    "status":"PROCESSADO COM PENDÊNCIAS" if info["pendencias"] else "PROCESSADO"})
                update(state,meta,records,info["eventos"])
                previous[url]=meta
                print("Processada",dt,"páginas",info["paginas"],
                      "registros",len(records),"pendências",len(info["pendencias"]),flush=True)
            except Exception as exc:
                total_errors+=1
                meta["pendencias"]=[str(exc)]
                # Não apagar dados bons por uma falha de rede posterior.
                if url not in previous:
                    update(state,meta,[])
                else:
                    # Preserve os registros e mantenha o erro visível para nova tentativa.
                    kept=copy.deepcopy(previous[url])
                    kept["status"]="PROCESSADO COM PENDÊNCIAS"
                    kept.setdefault("pendencias",[]).append("Falha de reprocessamento: "+str(exc)[:200])
                    for i,item in enumerate(state["edicoes"]):
                        if item.get("url")==url: state["edicoes"][i]=kept; break
                    previous[url]=kept
                print("ERRO",dt,str(exc),file=sys.stderr,flush=True)
            save_state(state,statefile)
        covered={x["url"] for x in state["edicoes"]
                 if completed(x)}
        remaining=sum(1 for e in editions if e["url"] not in covered)
        print(f"COBERTURA: edições descobertas {len(editions)}, processadas {len(covered)}, "
              f"pendentes no intervalo {remaining}, erros neste lote {total_errors}",flush=True)
        state["cobertura"]={"inicio":start.isoformat(),"fim":end.isoformat(),
            "edicoes_descobertas":len(editions),
            "edicoes_processadas_intervalo":len([e for e in editions if e["url"] in covered]),
            "edicoes_pendentes_intervalo":remaining,
            "ultima_execucao_erros":total_errors}
    save_state(state,statefile)
    build_html(state,Path(args.saida))
    print(f"Resultado: {len(state['registros'])} registros, {len(state['edicoes'])} edições; HTML em {args.saida}")
    return 2 if total_errors else 0
if __name__=="__main__":sys.exit(main())
