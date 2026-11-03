#!/usr/bin/env python3
"""Compara um recorte textual indexado com uma cópia privada de revisão.

Não baixa o PDF, não valida atos e não modifica o estado de entrada. O texto
informado precisa ser conferido como recorte da fonte oficial indicada.
"""
import argparse
import copy
import hashlib
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import robo


def _key(value):
    return re.sub(r"[^A-Z0-9]", "", robo.norm(value or ""))


def _same_resenha(value, expected):
    # O histórico também usa rótulos como "457/2026 · SEAD".
    match = re.match(r"^\s*(\d{1,5}/20\d{2})(?:\s*·|\s*$)", str(value or ""))
    return bool(match and match.group(1) == expected)


def compare(state, text, *, url, edition, page, resenha, consulted):
    """Retorna cópia anotada e contagens, sem promover candidatos.

    Só anota campos completos e coincidentes antes de outro cabeçalho ou
    PUBLIQUE-SE. A ordem do texto indexado pode misturar colunas, então a
    anotação é sempre preliminar e exige comparação ao PDF original.
    """
    if not robo.official_url(url):
        raise ValueError("A fonte deve ser uma URL oficial HTTPS de A União.")
    try:
        date.fromisoformat(edition)
        date.fromisoformat(consulted)
    except ValueError as exc:
        raise ValueError("Informe datas no formato AAAA-MM-DD.") from exc
    if not isinstance(page, int) or page < 1 or not re.fullmatch(r"\d{1,5}/20\d{2}", resenha):
        raise ValueError("Informe página e resenha válidas.")

    normalized = robo.norm(text)
    marks = list(robo.PAT_RES.finditer(normalized))
    selected = [i for i, mark in enumerate(marks) if mark.group(1) == resenha]
    if len(selected) != 1:
        raise ValueError("A resenha deve aparecer uma única vez no recorte textual.")
    index = selected[0]
    mark = marks[index]
    end = marks[index + 1].start() if index + 1 < len(marks) else len(normalized)
    segment = normalized[mark.start():end]
    boundary = re.search(r"(?m)^[ \t]*(?:PUBLIQUE[ \t]*-[ \t]*SE|SECRETARIA[ \t]+DE[ \t]+ESTADO\b)", segment)
    if boundary:
        segment = segment[:boundary.start()]

    first = robo.PAT_PROC.search(segment)
    if not first:
        raise ValueError("O recorte delimitado não contém processo reconhecível.")
    axis, modality, group, category = robo.hierarchy(segment)
    result = robo.merit(segment[:first.start()])
    source = robo.parse_rows(segment, edition, url, page, resenha, axis, modality,
                             group, category, result, "Original", "", False)
    source_by_key = {}
    duplicates = set()
    for row in source:
        k = _key(row.get("processo"))
        if k in source_by_key:
            duplicates.add(k)
        source_by_key[k] = row

    output = copy.deepcopy(state)
    candidates = [row for row in output.get("registros", [])
                  if row.get("fonte") == url and row.get("data") == edition
                  and _same_resenha(row.get("resenha"), resenha)
                  and row.get("pagina") == page
                  and not robo.reviewed(row) and not robo.rejected(row)]
    frequencies = {}
    for row in candidates:
        k = _key(row.get("processo"))
        frequencies[k] = frequencies.get(k, 0) + 1

    fields = ("matricula", "servidor", "eixo", "modalidade", "resultado")
    matches = []
    for row in candidates:
        k = _key(row.get("processo"))
        extracted = source_by_key.get(k)
        if not extracted or k in duplicates or frequencies[k] != 1:
            continue
        if not all(_key(extracted.get(field)) and _key(extracted.get(field)) == _key(row.get(field))
                   for field in fields):
            continue
        if extracted["resultado"] not in {"Deferido", "Indeferido"}:
            continue
        matches.append(row)

    mentions_gediv = bool(robo.PAT_GEDIV.search(segment))
    scope_note = ("A GEDIV aparece no recorte indexado; " if mentions_gediv else
                  "A GEDIV não foi identificada expressamente no recorte indexado; ")
    note = (f"Em {date.fromisoformat(consulted).strftime('%d/%m/%Y')}, processo, matrícula, nome, "
            f"eixo, modalidade e resultado coincidiram com o texto indexado da resenha {resenha}, "
            f"DOE de {date.fromisoformat(edition).strftime('%d/%m/%Y')}, página indicada {page}. "
            f"{scope_note}vínculo e PDF integral permanecem pendentes de conferência.")
    for row in matches:
        existing = str(row.get("conferencia_previa") or "")
        if note not in existing:
            row["conferencia_previa"] = (existing + " " + note).strip()
    summary = {"tipo": "texto_indexado", "data_consulta": consulted, "fonte": url,
               "pagina_indicada": page, "resenha": resenha, "registros_comparados": len(matches),
               "candidatos_no_historico": len(candidates), "processos_no_recorte": len(source_by_key),
               "gediv_expressa_no_recorte": mentions_gediv,
               "sha256_recorte_texto": hashlib.sha256(text.encode("utf-8")).hexdigest(),
               "limite": "Texto indexado informado; PDF integral e vínculo GEDIV permanecem pendentes."}
    output.setdefault("auditoria_previa", []).append(summary)
    return output, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("origem", "texto", "saida", "fonte", "data", "resenha"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--pagina", required=True, type=int)
    args = parser.parse_args(argv)
    original = json.loads(Path(args.origem).read_text(encoding="utf-8"))
    excerpt = Path(args.texto).read_text(encoding="utf-8")
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
    updated, result = compare(original, excerpt, url=args.fonte, edition=args.data,
                              page=args.pagina, resenha=args.resenha, consulted=today)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(args.saida, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(updated, ensure_ascii=False, indent=2))
    print(json.dumps({k: result[k] for k in ("resenha", "registros_comparados",
          "candidatos_no_historico", "processos_no_recorte", "gediv_expressa_no_recorte")},
          ensure_ascii=False))


if __name__ == "__main__":
    main()
