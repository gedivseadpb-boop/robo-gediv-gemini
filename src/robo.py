#!/usr/bin/env python3
"""Coletor conservador GEDIV: DOE-PB -> PDF -> registros auditáveis -> HTML.
Requer internet APENAS durante collect. PDFs locais funcionam sem rede.
"""
import argparse, hashlib, json, os, re, sys, time, unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
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
def fetch(url,session,max_bytes=25_000_000):
    for attempt in range(3):
        try:
            r=session.get(url,timeout=(15,60),headers={"User-Agent":"GEDIV-Monitor/1.0 (consulta pública; contato pelo repositório)"},stream=True)
            r.raise_for_status()
            data=b""
            for part in r.iter_content(65536):
                data+=part
                if len(data)>max_bytes: raise ValueError("Arquivo grande demais: "+url)
            return data
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
                if not href.startswith(BASE_URL): continue
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
    """Retorna trechos por coluna; OCR reforçado se não houver texto utilizável."""
    r=page.rect
    original=page.get_text("text",sort=True)
    if text_quality(original):
        # Separação de colunas evita mistura de resenhas de unidades diferentes.
        mid=(r.x0+r.x1)/2
        cols=[fitz.Rect(r.x0,r.y0,mid+8,r.y1),fitz.Rect(mid-8,r.y0,r.x1,r.y1)]
        return [(page.get_text("text",clip=col,sort=True),False) for col in cols]
    # PDF com fonte cifrada ou digitalizado: OCR com duas colunas
    mid=(r.x0+r.x1)/2
    cols=[fitz.Rect(r.x0,r.y0,mid+8,r.y1),fitz.Rect(mid-8,r.y0,r.x1,r.y1)]
    return [(ocr_pix(page,clip=col,scale=2.5,psm=6),True) for col in cols] + [(ocr_pix(page,scale=3,psm=6),True)]

def extract_rows_from_image(page):
    """Segunda passagem em faixas: necessária em tabelas com fonte pequena."""
    text=[]
    r=page.rect
    # Faixas com sobreposição preservam linhas horizontais.
    for y in range(0,int(r.height),70):
        rect=fitz.Rect(r.x0+20,r.y0+y,r.x1-20,min(r.y1,r.y0+y+112))
        line=ocr_pix(page,clip=rect,scale=5,psm=6)
        if PAT_PROC.search(norm(line)): text.append(line)
    return "\n".join(text)

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
            rest=flat[reg.end():]
            # Nome geralmente precede o cargo, mas não inventar se não identificável.
            job=re.search(r"\b"+JOBS+r"\b",rest,re.I)
            if job: name=compact(rest[:job.start()]).strip(" |-")
            else:
                # corta em cifras/títulos/fim de linha, e deixa pendente
                nm=re.match(r"([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÇ .'-]{5,75})",rest)
                if nm: name=nm.group(1).strip()
        if len(name)>90: name=""
        proc=compact(m.group()).replace(" ","").upper()
        row_result=merit(span)
        has_result=bool(re.search(r"\b(?:IN)?DEFERI(?:U|R|DO|DOS|DA|DAS|MOS)\b",norm(span)))
        effective=row_result if has_result else resultado
        unique=hashlib.sha256(f"{url}|{page_no}|{resenha}|{proc}|{effective}".encode()).hexdigest()[:20]
        rows.append({"id":unique,"data":dt,"resenha":resenha or "",
          "processo":proc,"servidor":name,"matricula":matricula,
          "eixo":eixo,"modalidade":modalidade,"grupo":grupo,"subcategoria":subcat,
          "resultado":effective,"alteracao":alteracao,"pagina":page_no,
          "fonte":url,"extracao":"OCR" if ocr else "Texto",
          "validacao":"PENDENTE — conferir PDF","trecho":compact(text[max(0,m.start()-70):m.end()+220])[:320]})
    return rows

def pdf_to_records(pdf,dt,url):
    rows=[]; events=[]; issues=[]; page_count=0; resenhas=set()
    with fitz.open(pdf) as document:
        page_count=len(document)
        for pno,page in enumerate(document,1):
            try:
                sections=page_sections(page)
                # Também avalia o texto completo: cabeçalhos podem atravessar as duas colunas
                complete="\n".join(t for t,_ in sections)
                for raw,ocr in sections:
                    text=norm(raw)
                    # Cabeçalho da GEDIV na própria coluna ou no topo da página
                    head=bool(PAT_GEDIV.search(text))
                    if not head: continue
                    # Conservar contexto GEDIV apenas até um cabeçalho de outra unidade.
                    idx=PAT_GEDIV.search(text).start()
                    prior=[m for m in PAT_RES.finditer(text[:idx]) if idx-m.end()<700]
                    candidate=text[prior[-1].start() if prior else idx:]
                    next_heading=re.search(r"\n\s*(?:SECRETARIA\s+DE\s+ESTADO|GERENCIA\s+EXECUTIVA\s+(?!DE\s+CONC|DE\s+DIREITOS|DE\s+CONCESSAO))",candidate[65:])
                    if next_heading: candidate=candidate[:65+next_heading.start()]
                    # Se o cabeçalho estiver fora do OCR de coluna, tente introdução da página inteira.
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
                        alt=alteration(act)
                        if alt!="Original":
                            event_id=hashlib.sha256(f"{url}|{pno}|{rid}|{alt}|{act}".encode()).hexdigest()[:20]
                            events.append({"id":event_id,"data":dt,"fonte":url,"pagina":pno,
                                "resenha_modificadora":rid,"tipo":alt,"validacao":"PENDENTE_VINCULACAO",
                                "trecho":compact(act)[:1000]})
                            continue
                        first_proc=PAT_PROC.search(act)
                        result=merit(act[:first_proc.start()] if first_proc else act)
                        if eixo=="Outras publicações GEDIV":
                            issues.append(f"p.{pno} resenha {rid or '?'}: tema fora dos dois eixos; revisar.")
                            continue
                        recs=parse_rows(act,dt,url,pno,rid,eixo,mod,grupo,sub,result,alt,"",ocr)
                        if not recs and ocr:
                            # OCR em faixas pequenas para recuperar as linhas da tabela.
                            fine=extract_rows_from_image(page)
                            recs=parse_rows(norm(fine),dt,url,pno,rid,eixo,mod,grupo,sub,result,alt,"",True)
                        if not recs: issues.append(f"p.{pno} resenha {rid or '?'}: sem processos extraídos; exige revisão.")
                        else:
                            rows+=recs
                            resenhas.add((dt,rid))
            except Exception as exc:
                issues.append(f"p.{pno}: falha de leitura {str(exc)[:120]}")
    # deduplicação mantendo alerta, nunca inventar valores em colisão
    clean={r["id"]:r for r in rows}
    unique_events={e["id"]:e for e in events}
    return list(clean.values()), {"paginas":page_count,"resenhas":len(resenhas),"pendencias":issues,"eventos":list(unique_events.values())}

def read_state(path):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: raise ValueError("Estado JSON inválido; faça backup antes de continuar")
    return {"edicoes":[],"registros":[],"eventos":[],"atualizado_em":None}
def save_state(state,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    state["atualizado_em"]=now()
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(path)
def update(state,meta,rows,events=None):
    by_url={x["url"]:x for x in state["edicoes"]}
    by_url[meta["url"]]=meta
    state["edicoes"]=list(by_url.values())
    # Se PDF mudou, substituir registros da edição (não somar versões antigas
    # de extração ao novo documento). A auditoria documental final requer modelo
    # de versões próprio; este coletor continua sendo protótipo.
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
    outdir.mkdir(parents=True,exist_ok=True)
    def write(filename,data):
        # substituição segura para tag JSON
        embedded=json.dumps(data,ensure_ascii=False).replace("<","\\u003c").replace("</","<\\/")
        (outdir/filename).write_text(template.replace("__GEDIV_EMBED_DATA__",embedded),encoding="utf-8")
    repo=os.getenv("GITHUB_REPOSITORY","")
    workflow_url=f"https://github.com/{repo}/actions/workflows/gediv.yml" if repo else ""
    write("painel_privado.html",{"mode":"privado","workflow_url":workflow_url,**state})
    # Não gerar uma cópia pública com linhas individuais.
    (outdir/"dados_agregados.json").write_text(json.dumps({"atualizado_em":state.get("atualizado_em"),"edicoes":len(state["edicoes"]),"decisoes":len(state["registros"])},ensure_ascii=False),encoding="utf-8")
def main(argv=None):
    ap=argparse.ArgumentParser(description="Robô GEDIV — DOE Paraíba")
    ap.add_argument("--inicio",default=(date.today()-timedelta(days=14)).isoformat())
    ap.add_argument("--fim",default=date.today().isoformat())
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
    statefile=Path(args.estado); state=read_state(statefile)
    if args.pdf:
        if not args.data_pdf: ap.error("--data-pdf é obrigatório com --pdf")
        pdf=Path(args.pdf)
        if not pdf.is_file(): ap.error("PDF não encontrado: "+str(pdf))
        url=args.url_pdf or "Documento fornecido para teste local — referência oficial não comprovada"
        rows,info=pdf_to_records(pdf,args.data_pdf,url)
        meta={"url":url,"data":args.data_pdf,"arquivo_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),"status":"PROCESSADO COM PENDÊNCIAS" if info["pendencias"] else "PROCESSADO","paginas":info["paginas"],"registros":len(rows),"pendencias":info["pendencias"]}
        update(state,meta,rows,info["eventos"])
        print("PDF local",json.dumps(meta,ensure_ascii=False),len(rows),"registros")
    else:
        start,end=date.fromisoformat(args.inicio),date.fromisoformat(args.fim)
        if end<start:ap.error("Intervalo inválido")
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
                 or not previous[e["url"]].get("status","").startswith("PROCESSADO")]
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
                    and existing.get("status","").startswith("PROCESSADO")):
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
                if url not in previous or not previous[url].get("status","").startswith("PROCESSADO"):
                    update(state,meta,[])
                print("ERRO",dt,str(exc),file=sys.stderr,flush=True)
            save_state(state,statefile)
        covered={x["url"] for x in state["edicoes"]
                 if x.get("status","").startswith("PROCESSADO")}
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
if __name__=="__main__":main()
