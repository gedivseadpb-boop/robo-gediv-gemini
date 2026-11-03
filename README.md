# Robô GEDIV — Diário Oficial da Paraíba

Projeto em desenvolvimento para localizar publicações da GEDIV no DOE-PB, preservar fontes e subsidiar um painel gerencial. A coleta e os resultados precisam de conferência humana. Esta branch é um piloto e não demonstra carga histórica completa ou rotina diária em produção.

## Conteúdo

- `src/robo.py`: descoberta de edições, leitura de PDF/OCR e geração do estado privado.
- `src/dashboard.py` e `painel-interativo/`: geração do painel gerencial privado a partir do estado do coletor. Somente registros conferidos entram nos indicadores.
- `src/revisar.py`: revisão manual de um estado JSON privado, com justificativa e rastreabilidade básica.
- `src/importar_historico.py`: adapta o catálogo anterior para um novo estado privado, sem promover registros a validados.
- `src/comparar_indice.py`: compara candidatos com um recorte textual indexado de fonte oficial e produz outra cópia privada, sem validá-los.
- `.github/workflows/gediv.yml`: rotina prevista para repositório privado.
- `.github/workflows/piloto-privado.yml`: teste isolado na branch do piloto, sem gravar o estado na branch principal.
- `.github/workflows/testes-piloto.yml`: testes automatizados isolados, sem coleta de dados de produção.
- `docs/CHECKLIST_PILOTO.md` e `docs/DIAGNOSTICO_E_EXECUCAO.md`: requisitos, evidências, limitações e próximos marcos.

## Executar testes locais

Com Python, PyMuPDF e as dependências do arquivo `requirements.txt` instalados:

```bash
python -m unittest discover -s tests -v
```

Os testes isolados não comprovam precisão do OCR nem cobertura do DOE. O processamento de páginas digitalizadas também precisa do Tesseract e do idioma português instalados. Páginas lidas por OCR ficam pendentes de conferência; o piloto não atribui automaticamente a uma resenha linhas obtidas da página inteira.

## Comparar um recorte indexado

Para triagem prévia, `src/comparar_indice.py` recebe o estado privado, um recorte textual já obtido, a URL oficial conferida, data, página indicada e resenha. Aceita apenas fonte oficial, recusa resenha repetida no recorte e anota coincidências completas em uma nova cópia, sem alterar o estado de origem nem a validação. Texto indexado pode misturar colunas; conferir o PDF integral, a página e o vínculo GEDIV continua obrigatório.

```bash
python src/comparar_indice.py --origem CAMINHO_PRIVADO/estado.json \
  --texto CAMINHO_PRIVADO/recorte.txt --saida CAMINHO_PRIVADO/estado_comparado.json \
  --fonte URL_OFICIAL_CONFERIDA --data AAAA-MM-DD --pagina NUMERO --resenha NUMERO/AAAA
```

## Preparar o catálogo histórico anterior para conferência

O JSON de origem não acompanha o repositório, pois pode conter dados individualizados. O comando abaixo cria um arquivo novo e não sobrescreve o anterior. As publicações e alterações importadas permanecem pendentes ou rejeitadas, ainda que o catálogo antigo as tenha marcado como validadas.

```bash
python src/importar_historico.py --origem CAMINHO_PRIVADO/catalogo_anterior.json \
  --estado-novo CAMINHO_PRIVADO/estado_revisao.json --saida CAMINHO_PRIVADO/painel
```

## Revisar um registro em um arquivo privado

O utilitário é opcional e exige conferência humana real no PDF e página oficial, além de responsável e justificativa. Trabalhe somente em uma cópia privada autorizada do estado. O comando modifica o JSON indicado e pode regenerar arquivos privados; não é um sistema de identidade ou de revisão multiusuário.

```bash
python src/revisar.py --estado CAMINHO_PRIVADO/estado.json --id ID_EXATO \
  --decisao validar --responsavel RESPONSAVEL --justificativa 'Conferência no PDF oficial' \
  --confirme-fonte --saida CAMINHO_PRIVADO/saida
```

Para rejeitar um candidato, use `--decisao rejeitar` e informe motivo. Uma versão de PDF substituída e ainda não resolvida não pode ser validada por esse comando.

## Segurança e operação

O repositório e os artefatos com dados funcionais devem permanecer privados. O arquivo `painel_gerencial_privado.html` contém os dados recebidos do estado: não publique o HTML nem o JSON em serviço público. Um HTML baixado não se atualiza sozinho.

## Conexão manual comprovada em 31/10/2026

O [painel privado de conferência](https://gediv-conferencia-privada-20261031.ylenaluna.chatgpt.site) recebeu três lotes reais, com 18 registros extraídos de recortes de fontes oficiais. A consulta autenticada confirmou 328 registros no total: 327 pendentes e um rejeitado. O reenvio do lote de 15 registros retornou `ja_recebido`, sem duplicação. As três extrações foram reproduzidas localmente com os mesmos registros e hashes de texto.

`src/extrair_texto.py` transforma texto já obtido em lote rastreável. O plugin privado do painel pode receber esse lote pela ferramenta `gediv_receber_lote` e verificar o resultado com `gediv_status`. Essa entrega foi testada contra o serviço real; não exige criar um token de acesso para esta conversa. `src/conectar_dashboard.py` é uma alternativa HTTP para ambiente com credencial de serviço já autorizada, ainda sem teste de entrega HTTP direta neste ambiente.

Veja [o fluxo de START manual e as evidências](docs/CONEXAO_MANUAL.md). A obtenção de texto indexado é assistida e parcial; o extrator não baixa esse texto por conta própria. Permanecem pendentes a leitura integral dos PDFs, OCR em português, carga histórica completa, revisão humana, acesso da equipe, exportações, automação diária e homologação. O agendamento continua desativado.
