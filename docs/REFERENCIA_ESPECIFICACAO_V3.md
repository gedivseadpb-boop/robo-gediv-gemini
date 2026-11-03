> **Referência funcional.** Documento de origem V3; confira decisões posteriores da usuária e o checklist atual quando houver divergências.

# ESPECIFICAÇÃO FUNCIONAL E DE AUDITORIA — ROBÔ GEDIV E DASHBOARD

**Versão:** 3.0 — consolidação das diretrizes comunicadas pela gerência em 29/10/2026  
**Situação:** especificação revisada; execução, coleta e indicadores **ainda não validados integralmente com documentos reais**.  
**Natureza:** requisitos de negócio aprovados pelo solicitante, não atestado de sistema implantado ou de publicação encontrada.

## 1. Finalidade, escopo e precedência

Monitorar edições oficiais do Diário Oficial do Estado da Paraíba, reconhecer somente publicações comprovadamente atribuídas à **Gerência Executiva de Concessão de Direitos e Vantagens (GEDIV/SEAD-PB)**, extrair decisões individuais, preservar documentos e suas alterações e apresentar informações gerenciais auditáveis.

Esta versão **substitui requisitos incompatíveis** dos documentos anteriores. Em especial: (a) existem **dois eixos**, não três; (b) Progressão Horizontal e Vertical são **modalidades do Eixo Progressão**; (c) dados individualizados só podem ser consultados por **usuários autorizados**, ainda que a fonte seja pública; (d) o cartão **REFEITOS** não mede retrabalho de processos; (e) não se considera o robô concluído sem validação em edições reais. Ficam preservadas as diretrizes compatíveis de layout, exportação, cobertura, leitura documental e segurança.

Fonte primária: [DOE — A União, edições](https://auniao.pb.gov.br/doe/diario-oficial-do-estado) e [acervo histórico](https://auniao.pb.gov.br/servicos/doe). Registrar endereço real do PDF após verificação; nunca fabricar URL. Identificar edição normal, suplemento e edição substitutiva, com data, número, páginas, hash SHA-256 e horário da coleta. Período histórico planejado: desde 01/01/2025, condicionado à disponibilidade e verificação das edições. Rotina diária é requisito futuro; não declarar automação em funcionamento antes de implantação e teste.

## 2. Taxonomia hierárquica, controlada e versionada

### Eixo 1 — Progressão Funcional

- Modalidade: **Horizontal**, **Vertical**, **Outra comprovada** (esta última somente após análise documental).
- Condição independente: **Plena**, **Condicional**, **Outra expressa**, **Não informada**.
- Grupo funcional/ocupacional: guardar **nome canônico**, **código**, **expressão original**, **status de validação**; código ausente = não informado.
- Dados de evolução: nível, classe e referência anteriores e posteriores, quando expressamente publicados.
- Grupos do catálogo inicial para busca: **Magistério (MAG)**; **Saúde (código ainda não confirmado no material disponível)**; **Apoio Judiciário (GAJ-1700)**; **Fiscalização Agropecuária (FAP-1300)**. Outros grupos encontrados nos levantamentos anteriores, como **ANS-900**, **Grupo Especial** e **DPS-1600**, permanecem sujeitos à evidência específica da publicação GEDIV e ao registro da variante oficial. Um grupo não é um órgão de lotação.
- Organização obrigatória da interface: `PROGRESSÃO → HORIZONTAL → GRUPOS` e `PROGRESSÃO → VERTICAL → GRUPOS`. **Grupo não é terceiro eixo.** Condição aparece como filtro ou dimensão auxiliar, não substitui modalidade.

### Eixo 2 — Tempo de Serviço

**Catálogo obrigatório de sete subcategorias já especificadas para o projeto:**

| Código | Subcategoria | Observação de governança |
|---|---|---|
| TS-01 | Anotação de Tempo de Serviço/Contribuição | Verificar expressão oficial em cada ocorrência |
| TS-02 | Desaverbação de Tempo de Serviço | Verificar expressão oficial em cada ocorrência |
| TS-03 | Licença para Tratar de Interesses Particulares | Classificar apenas se vínculo GEDIV estiver comprovado |
| TS-04 | Desistência de Licença de Interesse Particular | Classificar apenas se vínculo GEDIV estiver comprovado |
| TS-05 | Licença Especial | Classificar apenas se vínculo GEDIV estiver comprovado |
| TS-06 | Conversão de Licença Especial em Tempo de Serviço | Classificar apenas se vínculo GEDIV estiver comprovado |
| TS-07 | Conversão de Férias | Manter visível mesmo quando não houver registros verificados |

**Aprovação do catálogo não comprova ocorrência documental de todas as sete subcategorias.** Para ausência de registros, exibir **“sem ocorrência confirmada no período verificado”** somente se o período estiver integralmente conferido; caso contrário, exibir **“cobertura pendente”**. As denominações **Averbação de Tempo de Serviço/Contribuição**, **Revisão/Retificação de Tempo** e outros termos identificados em materiais anteriores permanecem na **fila de conceitos candidatos ou complementares**, sem criação automática de uma oitava categoria ou fusão sem autorização da GEDIV. Não confundir retificação de uma publicação com revisão substantiva de tempo de serviço.

Quando disponíveis: origem do tempo (privada, federal, estadual ou municipal), origem textual literal, data inicial/final, quantidade de dias, processo, decisão e trecho-fonte. Não classificar progressão como Tempo de Serviço por mera menção a tempo de exercício. Não incluir atos de outra gerência por afinidade temática.

**Dicionário versionado:** entidade `categoria_dicionario` com código, eixo, modalidade/subcategoria, condição, nome canônico, código do grupo, sinônimos, expressões originais, documento comprobatório, estado (`CONFIRMADA`, `PROVISORIA`, `CANDIDATA`, `DESATIVADA`), revisor, data e versão. Novas denominações entram como **candidatas**, não alteram automaticamente classificação oficial nem agregados.

## 3. Identificação GEDIV em duas camadas

**Camada institucional:** detectar o cabeçalho e alcance do bloco/resenha/ato. Buscar nome completo, abreviações e siglas contextualizadas. O termo `DEREH`, `SEAD` ou uma lotação isolada **não comprova GEDIV**. Evitar associação de texto de outras colunas, páginas ou resenhas. Guardar a expressão e posição que demonstram o vínculo, página e PDF oficial.

**Camada temática:** somente após comprovação institucional classificar eixo, modalidade/subcategoria, condição, grupo, processo e resultado. Ocorrências temáticas sem comprovação institucional entram em fila `INDICIO_SEM_VINCULO` para validação e **não alimentam cartões da GEDIV**.

Busca textual adicional por `RETIFICAÇÃO`, `RETIFICA-SE`, `RETIFICO`, `REPUBLICAÇÃO`, `REPUBLICADO POR INCORREÇÃO`, `CORREÇÃO`, `ONDE SE LÊ`, `LEIA-SE`, `TORNAR SEM EFEITO`, `TORNADO SEM EFEITO`; aceitar variantes de caixa, acentuação e flexão para triagem. **Palavra-chave é gatilho, não prova.** Confirmar GEDIV e alcance da expressão no ato específico.

## 4. Três dimensões independentes de classificação

**A — Resultado do mérito:** `DEFERIDO`, `INDEFERIDO`, `OUTRO_COMPROVADO`, `NAO_INFORMADO`. Extrair verbo e contexto do próprio ato; resultado de uma linha não se propaga para outra.

**B — Alteração da publicação:** `ORIGINAL`, `RETIFICADA`, `CORRIGIDA`, `REPUBLICADA`, `TORNADA_SEM_EFEITO`. Exibir o **estado documental mais recente conhecido** de cada ato e manter todas as mudanças em histórico imutável; `REPUBLICADO_POR_INCORRECAO` é subtipo/descritor de evento `REPUBLICADA`. Caso exista evento de efeito não mapeável, registrar literal e manter pendência.

**C — Indicador REFEITOS:** `SIM` se existir **ao menos um evento validado e vinculado** de retificação, correção ou republicação (inclusive por incorreção), ou equivalente documental aprovado para essa classe; `NÃO` na ausência de tais eventos vinculados na base verificada. `NÃO` **não significa prova de inexistência** se houver lacunas de cobertura. Eventos `TORNADA_SEM_EFEITO` **não fazem REFEITOS virar SIM por si sós**. Manter indicador específico de atos tornados sem efeito. Um mesmo ato pode ser simultaneamente REFEITO e TORNADO SEM EFEITO, se houver ambos os eventos comprovados.

Jamais interpretar REFEITOS como processo reavaliado/retrabalhado internamente. A data relevante para o indicador é a **publicação do evento modificador**, não a data do ato original ou do expediente administrativo.

## 5. Modelo lógico de dados e integridade

Entidades mínimas (chaves estáveis sem pressupor equivalência entre entidades):

1. `edicao_doe`: id, data, edição, suplemento, URL oficial, hash SHA-256, situação de leitura, páginas, coleta.
2. `documento_pagina`: edição, página física e impressa, blocos, posições, extração textual, qualidade e evidências.
3. `ato_original`: `ato_original_id`, tipo (resenha/ato individual), unidade autora comprovada, número de resenha, data, edição, página, URL, trecho original, validação.
4. `resenha`: `resenha_id`, número/ano, ato publicador, data de publicação, abrangência; uma resenha pode conter muitas decisões.
5. `processo`: `processo_id`, identificador textual e normalizado **sem fusão automática de homônimos/numerações ambíguas**.
6. `decisao_individual`: `decisao_id`, `ato_original_id`, `resenha_id`, `processo_id` quando comprovado, servidor, matrícula, eixo, modalidade/subcategoria, condição, grupo, classe/nível/referência, mérito, evidência, validação.
7. `evento_alteracao`: `evento_id`, `tipo_evento`, subtipo, `data_publicacao_evento`, identificação de resenha/ato modificador, texto literal, descrição da correção, URL e página, hash, validação.
8. `vinculo_alteracao`: `evento_id`, `ato_original_id` e, quando determinável, `decisao_id`, fundamento textual do pareamento, grau de segurança, revisor e estado (`VALIDADO`, `PENDENTE_VINCULACAO`, `REJEITADO`). Um evento pode alcançar vários atos/decisões e um ato pode ter múltiplos eventos.
9. `versao_publicacao`: `versao_id`, `ato_original_id`, `evento_id` se aplicável, versão anterior, texto/valores identificados e documento-fonte. **Nunca sobrescrever versão anterior.**
10. `dicionario_classificacao`, `log_execucao`, `fila_validacao`, `controle_acesso`, `auditoria_consulta_exportacao`.

**Pareamento seguro:** número/ano da resenha, referência ao ato anterior, servidor, matrícula, processo, objeto e dados textuais podem formar evidência combinada; **não parear apenas por nome ou processo parecido**. Se o DOE não possibilitar correspondência inequívoca, armazenar o evento com `PENDENTE_VINCULACAO` e seu PDF, mas **não atribuí-lo** a ato/processo/servidor nem incrementá-lo indevidamente no cartão REFEITOS. Reportar contagem separada de **eventos modificadores não vinculados**, para que a subcontagem seja visível.

**Situação atual:** recompor as versões em ordem cronológica documental e considerar o **último ato válido com correspondência comprovada**. Quando houver evento posterior pendente, exibir `SITUACAO_SOB_REVISAO`, preservando o último estado confirmado e explicando a limitação. Em empate de data, usar referência documental ou ordenação oficial comprovada; nunca inventar precedência. O estado de mérito pode mudar; sempre preservar mérito publicado originalmente e mérito vigente documentalmente reconhecido.

## 6. Contrato de indicadores — unidade, datas e deduplicação

Todos os cartões recebem filtros autorizados e mostram unidade e regra de data na ajuda contextual. Para evitar misturar datas de atos originais com alterações, aplicar **tempo específico por indicador**:

| Cartão | Unidade de contagem | Data de seleção | Regra |
|---|---|---|---|
| Total de processos | `COUNT(DISTINCT processo_id)` vinculado a decisões elegíveis | Publicação inicial da decisão no período | Não contar republicação como processo novo |
| Total de resenhas | `COUNT(DISTINCT resenha_id)` de resenhas originais GEDIV elegíveis | Publicação original | Não duplicar por retificação/republicação |
| Total de decisões individuais | `COUNT(DISTINCT decisao_id)` elegível | Publicação original da decisão | Não converter evento em nova decisão |
| Deferidos | `COUNT(DISTINCT decisao_id)` com resultado de mérito atual validado `DEFERIDO` | Publicação original da decisão | Respeitar situações pendentes e versões |
| Indeferidos | `COUNT(DISTINCT decisao_id)` com resultado de mérito atual validado `INDEFERIDO` | Publicação original da decisão | Mesmo critério de Deferidos |
| Refeitos | `COUNT(DISTINCT ato_original_id)` com ao menos um vínculo **validado** a evento retificação/correção/republicação | **Data da publicação do evento modificador** | Contar ato uma única vez no período, mesmo com diversos eventos |
| Tornados sem efeito | `COUNT(DISTINCT ato_original_id)` com evento validado `TORNADA_SEM_EFEITO` | **Data da publicação do respectivo evento** | Indicador independente; pode sobrepor-se a Refeitos |

**Métrica adicional obrigatória:** `Total de eventos de alteração = COUNT(DISTINCT evento_id)` para eventos validados de retificação/correção/republicação no período, inclusive quando vários eventos atingem o mesmo ato. Exibir por tipo. A lista de eventos pendentes de vinculação é separada, sem contaminação dos totais de atos comprovadamente afetados.

**Atenção à cardinalidade:** uma retificação de resenha só aumenta `REFEITOS` para atos originais cujo alcance esteja documentalmente demonstrado. Se a retificação afetar exclusivamente parte das linhas, não presumir alteração de todas as decisões; se a unidade original modificada for identificável apenas como resenha inteira, registrar essa granularidade e indicar a pendência quanto às linhas. `ato_original_id` deve identificar de forma consistente a **unidade documental alterada**, não transformar automaticamente cada linha em ato distinto.

**Exemplo de período:** ato original publicado em dezembro/2025 e retificado em outubro/2026 **entra em Refeitos de outubro/2026**; não entra automaticamente nos cartões de processos/decisões originais de outubro/2026. Se houver duas retificações e uma republicação no mesmo período, `Refeitos = 1 ato` e `Eventos de alteração = 3` (supondo que cada evento seja distintamente comprovado).

**Sobreposição:** não somar Deferidos + Indeferidos + Refeitos + Tornados sem efeito para produzir total geral. Tampouco somar processos, decisões e resenhas. Para recortes históricos, esclarecer que Deferidos/Indeferidos exibem a **última situação de mérito documental validada conhecida**, enquanto o filtro de período considera a publicação original; uma eventual visualização “situação na data” exigirá regra própria e dados históricos completos.

**Nota de cobertura:** ausência de evento comprovado não deve ser divulgada como certeza de inexistência; mostrar edições lidas, falhas, suplementos pendentes, alterações não vinculadas e data do corte. Um valor zero requer cobertura suficiente para o recorte.

## 7. Comportamento do dashboard

Preservar identidade institucional já aprovada: inspiração Power BI, cabeçalho institucional, **filtros recolhíveis à esquerda**, gráficos e **sete cartões no centro**, **tabela analítica à direita**; interface responsiva, registros expansíveis e **tela cheia**. O layout anterior de três eixos é substituído por dois eixos; os gráficos históricos deverão ser reconfigurados para `Progressão` e `Tempo de Serviço`, com horizontal/vertical **dentro** de Progressão.

**Sete cartões clicáveis:** Total de processos; Total de resenhas; Total de decisões individuais; Deferidos; Indeferidos; **Refeitos**; Tornados sem efeito. Cada clique aplica um filtro sobre a tabela para **exclusivamente o universo do indicador**, com possibilidade de desfazer seleção, preservação dos demais filtros e respeito à segurança. Não mostrar um registro apenas porque compartilha o mesmo processo se não satisfizer a métrica clicada. Exibir cartões de apoio para quantidade de eventos modificadores, eventos sem vínculo e cobertura, sem alterar a lista dos sete principais.

**Filtros:** período (com semântica própria por indicador), eixo, modalidade, condição, grupo, subcategoria, mérito, tipo de alteração, validação, resenha, processo, servidor e matrícula (os últimos sujeitos à autorização). Filtros contextuais devem ser neutros onde a dimensão não se aplica, e não atribuir artificialmente grupo a Tempo de Serviço. Para registros modificados, usar dimensões do ato original/estado atual **validado**; sinalizar dimensões alteradas e pendentes de revisão. Tabelas, gráficos e cartões deverão executar a mesma política de filtros e autorização, respeitando a unidade de contagem de cada métrica.

**Navegação:** Visão Geral; Progressão (Horizontal/Vertical e grupos); Tempo de Serviço (sete subcategorias); Publicações do Dia; Histórico; **Alterações/Refeitos**. Manter dois modos da tabela: `POR RESENHA` e `POR PROCESSO`, sem alterar a contagem de cartões. Expandir/recolher resenha, processo e encadeamento de versões; abrir a lista filtrada em tela cheia.

**Ao clicar REFEITOS:** tabela com `data_alteracao`, `resenha_original`, `resenha_ou_ato_modificador`, `servidor`, `processo`, `eixo`, `modalidade_ou_subcategoria`, `grupo_funcional_se_aplicavel`, `tipo_alteracao`, `descricao_correcao`, `link_original`, `pagina_original`, `link_modificador`, `pagina_modificador`, `estado_validacao`, `ato_original_id`, `quantidade_eventos`. Cada **ato original aparece uma vez** na contagem e na visão resumida; expansão exibe **todos os eventos em ordem cronológica**. A visualização `POR PROCESSO` pode mostrar agrupamentos repetidos por perspectiva, mas a contagem permanece por `ato_original_id`. Abrir PDF oficial e, quando possível, a página exata; ausência de URL/página = “não informado/pendente”.

**Exportação:** Excel dos dados filtrados completos (não apenas página da tabela), com abas para `Atos`, `Decisoes`, `Eventos_de_Alteracao`, `Vinculos`, `Pendencias` e `Metadados` quando pertinentes. Inclua datas e filtros, origem/página, cobertura, instante do processamento, versão do dicionário. Aplicar permissão de exportação e proteção contra fórmulas injetadas. As exportações de gráficos/página para PDF/PNG anteriormente especificadas permanecem requisitos compatíveis, condicionados à implementação e à autorização.

## 8. Processamento, segurança e qualidade

**Pipeline:** descobrir edições (incluindo suplementos) → verificar PDF e hash → extrair texto por blocos/colunas → reconhecer GEDIV institucionalmente → segmentar resenhas/atos → extrair decisões individuais → buscar eventos modificadores → relacionar original/modificador com evidência → versionar → classificar → validar pendências → disponibilizar resultados e indicadores sob controle de acesso.

Preferir método determinístico, leitura correta de colunas e uso limitado de OCR para regiões ilegíveis; nunca misturar verbos/linhas entre atos. Distinguir número e data do DOE da data do expediente. Validar páginas físicas/impressas, identidades, processos e duplicidades. Reprocessar somente quando necessário, conservando histórico de mudanças de extração e revisão.

**Segurança/LGPD:** dashboards agregados podem ser disponibilizados conforme avaliação institucional; **nome de servidor, matrícula, processo e detalhes individualizados ficam restritos a perfis autorizados**, inclusive pesquisas, tabelas, APIs e exportações. Autenticação e autorização no servidor, política de minimização de dados, logs de acesso, revisão periódica de permissões e proteção de arquivos. A existência de informação no DOE não autoriza republicação ilimitada em índice pesquisável. Não enviar dados internos a provedores externos sem base e autorização.

**Auditoria:** preservar texto literal que sustenta vínculo institucional, categoria, mérito e alteração; versões anteriores; PDF oficial/hash; data/hora de coleta; mecanismo de extração; revisor; motivo de inclusão/exclusão; idempotência; eventos não vinculados; cobertura por edição. Nunca contar outra gerência por palavra-chave isolada.

## 9. Cenários mínimos de aceitação (dados de teste hipotéticos, NÃO publicações reais)

| Cenário | Esperado |
|---|---|
| Ato A retificado duas vezes e republicado uma vez no mesmo mês | Refeitos 1; eventos de alteração 3; processo original sem duplicação |
| Ato original em 2025 alterado em outubro de 2026 | Conta em Refeitos de outubro/2026; não cria processo original de outubro |
| Ato B somente tornado sem efeito | Refeitos 0; Tornados sem efeito 1 |
| Ato C retificado e depois tornado sem efeito | Refeitos 1; Tornados sem efeito 1; histórico com 2 eventos |
| Evento com “ONDE SE LÊ/LEIA-SE”, sem comprovação GEDIV | Excluído dos totais GEDIV; indício em fila de validação |
| Evento GEDIV confirmado, mas ato anterior não identificado | Evento e documento preservados como `PENDENTE_VINCULACAO`; não atribuir processo nem elevar Refeitos |
| Resenha com 3 linhas decisórias e 2 processos distintos | 1 resenha; 3 decisões; 2 processos, após validação |
| Mesmo processo em original e republicação | 1 processo distinto; versões e eventos preservados |
| Filtro Progressão > Horizontal > MAG | Somente registros elegíveis; não promover MAG a eixo |
| Filtro Tempo de Serviço > Conversão de Férias, sem leitura completa | Exibir cobertura pendente, não zero confirmado |
| Usuário sem acesso individualizado clica ou exporta | Somente agregados permitidos; API bloqueia acesso às linhas |
| Versão modificadora altera o resultado de mérito | Histórico preservado; situação atual reflete último ato válido comprovado; sinalizar pendências |

**Aceitação de produção:** somente depois de comparar, por amostras suficientes e registradas de edições reais, o resultado do robô com revisão humana para (1) identificação GEDIV, (2) completude de resenhas e decisões, (3) sete subcategorias, (4) grupos e condições, (5) ligações original-modificador, (6) contagem e filtros, (7) rastreabilidade, (8) segurança/exportação. Apurar precisão, revocação e taxa de erros com denominadores documentados; não inventar percentuais ou alegar “100%”.

## 10. Próxima etapa prioritária

1. **Inventariar e validar grupos funcionais de Progressão** e códigos/variantes com resenha, página e PDF oficiais; não presumir catálogo exaustivo.
2. **Validar publicações oficiais GEDIV**, especialmente atos originais e seus modificadores, com identificação institucional em duas camadas e fila de correspondências pendentes.
3. Construir um conjunto de referência anotado por humanos para testes dos sete cartões, dos eventos de alteração e da cobertura de edições.
4. Só então desenvolver/colocar em operação os indicadores no dashboard e o agendamento de coleta, com comprovação de funcionamento.

**Status final:** requisitos revisados e organizados; **robô não concluído; dashboard não considerado validado ou em produção**.