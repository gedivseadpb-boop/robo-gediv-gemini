"""Converte o estado privado do coletor para o painel gerencial independente.

Apenas registros expressamente conferidos entram em indicadores. Este arquivo
HTML contém dados funcionais e deve permanecer sob acesso autorizado.
"""
import base64
import hashlib
import json
import os
import unicodedata
from pathlib import Path

CATEGORIES = [
    ["TS-01", "Anotação de Tempo de Serviço/Contribuição"],
    ["TS-02", "Desaverbação de Tempo de Serviço"],
    ["TS-03", "Licença para Tratar de Interesses Particulares"],
    ["TS-04", "Desistência de Licença de Interesse Particular"],
    ["TS-05", "Licença Especial"],
    ["TS-06", "Conversão de Licença Especial em Tempo de Serviço"],
    ["TS-07", "Conversão de Férias"],
]
CATEGORY_CODES = {
    "Anotação de Tempo": "TS-01",
    "Desaverbação": "TS-02",
    "Licença para Interesses Particulares": "TS-03",
    "Desistência de Licença": "TS-04",
    "Licença Especial": "TS-05",
    "Conversão de Licença Especial": "TS-06",
    "Conversão de Férias": "TS-07",
}


def _norm(value):
    return "".join(c for c in unicodedata.normalize("NFKD", str(value or ""))
                   if not unicodedata.combining(c)).upper().strip()


def validation(value):
    value = _norm(value)
    if value in {"VALIDADO", "VALIDADA", "CONFERIDO", "CONFERIDA"}:
        return "conferido"
    if value in {"REJEITADO", "REJEITADA", "EXCLUIDO", "EXCLUIDA"}:
        return "rejeitado"
    return "pendente"


def _resenha_id(row):
    if row.get("resenha_id"):
        return str(row["resenha_id"])
    resenha = str(row.get("resenha") or "").strip()
    if not resenha:
        return ""
    key = "|".join(str(row.get(x) or "") for x in ("fonte", "data", "resenha"))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _row(row):
    axis = {"Progressão": "progressao", "Tempo de Serviço": "tempo"}.get(
        row.get("eixo"), "outros")
    merit = {"DEFERIDO": "deferido", "INDEFERIDO": "indeferido"}.get(
        _norm(row.get("resultado")), "outro")
    # Não atribuir códigos ocupacionais ausentes do ato publicado.
    group = _norm(row.get("grupo"))
    return {
        "id": str(row.get("id") or ""),
        "date": str(row.get("data") or ""),
        "resenha": str(row.get("resenha") or ""),
        "resenha_id": _resenha_id(row),
        "process": str(row.get("processo") or ""),
        "server": str(row.get("servidor") or ""),
        "registration": str(row.get("matricula") or ""),
        "axis": axis,
        "modality": str(row.get("modalidade") or ""),
        "group": group,
        "category": CATEGORY_CODES.get(row.get("subcategoria"), ""),
        "merit": merit,
        "page": row.get("pagina") if row.get("pagina_confirmada_origem") is not False else None,
        "url": str(row.get("fonte") or ""),
        "evidence": str(row.get("trecho") or ""),
        "sourceMention": str(row.get("mencao_gediv_origem") or ""),
        "preliminaryReview": str(row.get("conferencia_previa") or ""),
        "act": str(row.get("ato_original_id") or ""),
        "validation": validation(row.get("validacao")),
    }


def _event(event):
    # Um evento só pode chegar aos cartões se o vínculo explícito foi revisado.
    act = str(event.get("ato_original_id") or "")
    reviewed = validation(event.get("validacao")) == "conferido"
    kind = str(event.get("tipo") or "")
    valid_kind = {"Retificação", "Correção", "Republicação", "Tornado sem efeito"}
    return {
        "id": str(event.get("id") or ""),
        "date": str(event.get("data") or ""),
        "act": act,
        "type": kind,
        "description": str(event.get("trecho") or ""),
        "url": str(event.get("fonte") or ""),
        "page": event.get("pagina") if event.get("pagina_confirmada_origem") is not False else None,
        "validation": "conferido" if reviewed and act and kind in valid_kind else "pendente",
    }


def adapt_state(state, workflow_url=""):
    rows = [_row(r) for r in state.get("registros", [])]
    events = [_event(e) for e in state.get("eventos", [])]
    editions = state.get("edicoes", [])
    confirmed = sum(r["validation"] == "conferido" for r in rows)
    pending = sum(r["validation"] == "pendente" for r in rows)
    rejected = sum(r["validation"] == "rejeitado" for r in rows)
    incomplete = sum(e.get("status") != "PROCESSADO" or bool(e.get("pendencias")) for e in editions)
    coverage = (f"{len(editions)} documento(s) registrado(s); {incomplete} com leitura ou revisão pendente. "
                "Cobertura integral do período ainda não foi homologada.")
    imported = state.get("importacao") or {}
    if imported:
        coverage = (f"Catálogo anterior de {imported.get('inicio_origem') or 'data não informada'} "
                    f"a {imported.get('fim_origem') or 'data não informada'}: {len(editions)} documento(s), "
                    f"{incomplete} com leitura ou revisão pendente. Cobertura integral não homologada.")
    return {
        "rows": rows,
        "events": events,
        "categories": CATEGORIES,
        "groups": [],
        "urls": {"workflow": workflow_url},
        "meta": {
            "version": "Painel privado · histórico em revisão" if imported else "Painel privado · validação pendente",
            "dictionary": "Catálogo inicial sujeito à conferência",
            "verifiedAt": state.get("atualizado_em"),
            "coverage": coverage,
            "automation": ("Cópia histórica para conferência; não se atualiza sozinha e a rotina diária ainda não foi comprovada."
                           if imported else "Arquivo gerado por lote; atualize e baixe uma nova cópia após outra execução."),
            "personal": "Contém dados funcionais; mantenha este arquivo em acesso restrito.",
            "semBaseCarregada": confirmed == 0,
            "edicoes": len(editions),
            "edicoesPendentes": incomplete,
            "conferidos": confirmed,
            "pendentes": pending,
            "rejeitados": rejected,
            "eventosPendentes": sum(e["validation"] == "pendente" for e in events),
        },
    }


def build_interactive_html(state, root, outdir, workflow_url=""):
    root, outdir = Path(root), Path(outdir)
    directory = root / "painel-interativo"
    template = (directory / "index.html").read_text(encoding="utf-8")
    css = (directory / "styles.css").read_text(encoding="utf-8")
    exporter = (directory / "export.js").read_text(encoding="utf-8")
    app = (directory / "app.js").read_text(encoding="utf-8")
    logo = base64.b64encode((directory / "logo.png").read_bytes()).decode("ascii")
    payload = json.dumps(adapt_state(state, workflow_url), ensure_ascii=False, separators=(",", ":"))
    # Proíbe que texto extraído do PDF termine a tag script ou injete marcação.
    payload = (payload.replace("<", "\\u003c").replace(">", "\\u003e")
               .replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
    replacements = {
        '<link rel="stylesheet" href="styles.css">': '<style>' + css + '</style>',
        'src="logo.png"': 'src="data:image/png;base64,' + logo + '"',
        '<script src="data.js"></script>': '<script>window.GEDIV_DATA=' + payload + ';</script>',
        '<script src="export.js"></script>': '<script>' + exporter + '</script>',
        '<script src="app.js"></script>': '<script>' + app + '</script>',
    }
    for before, after in replacements.items():
        if template.count(before) != 1:
            raise ValueError("Estrutura inesperada do painel: " + before)
        template = template.replace(before, after)
    outdir.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = outdir / "painel_gerencial_privado.html"
    flags=os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,"O_NOFOLLOW",0)
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as stream:
        if hasattr(os,"fchmod"): os.fchmod(stream.fileno(),0o600)
        stream.write(template)
    return path
